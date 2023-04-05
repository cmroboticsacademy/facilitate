from collections.abc import Callable
from enum import Enum

OpCodes = Enum('OpCodes', ["spike_movemenet_direction_for_duration",
    "spike_movemenet_direction",
    "spike_movement_moveHeadingForUnits",
    "spike_movement_startMoving",
    "spike_movement_stopMoving",
    "spike_movement_moveHeadingForUnitAtSpeed",
    "spike_movement_moveForUnitsAtSpeeds",
    "spike_movement_setMovementSpeed",
    "spike_movement_startMovingHeadingAtSpeed",
    "spike_movement_startMovingAtSpeeds",
    "spike_motor_runForDirectionTimes",
    "spike_motor_runDirection",
    "spike_motor_stopMotor",
    "spike_motor_position",
    "spike_light_turnOnForSeconds",
    "spike_set_pixel_brightness",
    "spike_write",
    "spike_sensor_is_pressed",
    "spike_sensor_force",
    "spike_sensor_is_distance",
    "spike_sensor_distance",
    "spike_sensor_reflected_light_intensity",
    "spike_sensor_is_reflected_light",
    "spike_sensor_is_color",
    "spike_sensor_color",
    "spike_sensor_reset_yaw",
    "spike_sensor_angle",
    "spike_sensor_is_orientation",
    "spike_sensor_is_moved",
    "spike_sensor_is_button",
    "spike_sensor_timer",
    "spike_sensor_reset_timer",
    "spike_sound_playuntildone",
    "spike_sound_startsound",
    "spike_play_beep",
    "spike_start_playing_beep",
    "spike_stop_all_sounds",
    "spike_set_volume",
    "event_whenprogramstarts",
    "spike_sensor_motor_menu",
    "spike_direction_picker",
    "spike_movement_direction_picker",
    "spike_heading_input",
    "spike_sensor_port_menu",
    "spike_sensor_color_menu"])

class ASTNode(dict):
    def __init__(self):
        self.parent = None
        self.blockid = None
        self.op = None
        self.name = self.op # for visualization
        self.children = []
        self.next = None
        self.inputs = []
        self.fields = []
        self._height = 1
        self.attributes = {}
        dict.__init__(self, 
            blockid = self.blockid,
            op = self.op,
            name = self.name,
            children = self.children,
            _height = self._height,
            attributes = self.attributes)
        
    def __init__(self, parent, blockid, desc, next=[], inputs=[], fields=[]):
        self.parent = parent
        self.blockid = blockid
        self.op = desc
        self.name = self.op # for visualization
        self.next = sorted(next, key=lambda n: str(n.op))
        self.inputs = sorted(inputs, key=lambda n: str(n.op))
        self.fields = sorted(fields, key=lambda n: str(n.op))
        self.children = self.inputs + self.fields + self.next
        self._height = self.__height__()
        self.attributes = {}
        dict.__init__(self, 
            blockid = self.blockid,
            op = self.op,
            name = self.name,
            children = self.children,
            _height = self._height,
            attributes = self.attributes)

    def add_child(self, child:'ASTNode', childtype="next"):

        if childtype == "next":
            self.next.append(child)
            self.next = sorted(self.next, key=lambda n: str(n.op))
        elif childtype == "inputs":
            self.inputs.append(child)
            self.inputs = sorted(self.inputs, key=lambda n: str(n.op))
        elif childtype == "fields":
            self.fields.append(child)
            self.fields = sorted(self.fields, key=lambda n: str(n.op))
        else:
            raise ValueError("Child type " + childtype + " is not valid")

        self.children = self.inputs + self.fields + self.next

        super().update({"children": self.children})

        self.update_height()
    
    def remove_child(self, child:'ASTNode'):
        self.next.remove(child)
        self.inputs.remove(child)
        self.fields.remove(child)
        self.children = self.inputs + self.fields + self.next

        super().update({"children": self.children})

        self.update_height()


    def accept_no_children(self, visit_func:Callable[['ASTNode'],None]):
        visit_func(self)
    
    def accept(self, visit_func:Callable[['ASTNode'],None]):
        visit_func(self)
        for c in self.children:
            c.accept(visit_func)
            
    def accept_postorder(self, visit_func:Callable[['ASTNode'],None]):
        for c in self.children:
            c.accept(visit_func)
        visit_func(self)

    
            
    def __eq__(self, other:'ASTNode'):
        return self.blockid == other.blockid

    def subtree_equals(self, other:'ASTNode'):
        if not self.node_equals(other):
            return False
        if self.__height__() != other.__height__():
            return False
        if len(self.next) != len(other.next):
            return False
        for next1, next2 in zip(self.next, other.next):
            if not next1.subtree_equals(next2):
                return False
        return True

    def node_equals(self, other:'ASTNode'):
        if self.op != other.op:
            return False
        if len(self.inputs) != len(other.inputs):
            return False
        if len(self.fields) != len(other.fields):
            return False

        # gonna assume that chidren are sorted
        for i in range(len(self.inputs)):
            if not self.inputs[i].node_equals(other.inputs[i]):
                return False
        for i in range(len(self.fields)):
            if not self.fields[i].node_equals(other.fields[i]):
                return False
        return True

    def update_height(self):
        self._height = self.__height__()
        super().update({"_height" : self._height})
        if isinstance(self.parent, ASTNode):
            self.parent.update_height()
    
    def __height__(self):
        if len(self.children) == 0:
            return 1
        return max([c._height for c in self.children]) + 1
    
    def height(self):
        return self._height
    
    def count_subtree_occurences(self, other:'ASTNode'):
        if other._height > self._height:
            return 0
        if self.subtree_equals(other):
            return 1
        counter = 0
        for c in self.children:
            counter += c.count_subtree_occurences(other)
        return counter
        
    def iter_descendants(self):
        yield self
        for c in self.children:
            yield from c.iter_descendants()
            
    def get_descendants(self):
        return [s for s in self.iter_descendants()]
    
    def __str__(self):
        return f"ASTNode: {self.blockid} {self.op}\n\tParent: {self.parent.blockid if self.parent else None}, {len(self.children)} children"

    def __hash__(self):
        return hash(self.blockid)

    def copy(self):
        copied_next = [n.copy() for n in self.next]
        copied_inputs = [n.copy() for n in self.inputs]
        copied_fields = [n.copy() for n in self.fields]
        return ASTNode(self.parent, self.blockid, self.op, next=copied_next, inputs=copied_inputs, fields=copied_fields)

    def copy_no_children(self):
        return ASTNode(self.parent, self.blockid, self.op)