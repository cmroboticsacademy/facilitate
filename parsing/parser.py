from parsing.ast import ASTNode, OpCodes

def build_ast_tree(program_blocks:dict):
    root_node = None
    nodes = {} # block id: node
    to_parse_queue = program_blocks.copy()
    while len(to_parse_queue) > 0:
        blockid, block  = to_parse_queue.popitem()
        node = parse_block(blockid, block, nodes, to_parse_queue)
        
        if block["topLevel"] and node.op == OpCodes.event_whenprogramstarts:
            root_node = node
    return root_node


def parse_block(blockid, block, nodes, to_parse_queue):
    parent_id = block["parent"]
    oc = block["opcode"]
    try:
        desc = OpCodes[oc]
    except:
        desc = oc
    child_id = block["next"]
    
    node = ASTNode(None, blockid, desc, [])
    nodes[blockid] = node
    
    if parent_id in nodes:
        node.parent = nodes[parent_id]
        nodes[parent_id].children.append(node)
        
    if child_id in nodes:
        node.children.append(nodes[child_id])
    
    for k, v in block["fields"].items():
        id_num = blockid + "_field_"+str(k)
        value = v[0]
        field_node = ASTNode(None, id_num, k, [])
        field_child_node = ASTNode(field_node, id_num+"_value", value, [])
        field_node.children.append(field_child_node)
        node.children.append(field_node)
        
    for k, v in block["inputs"].items():
        id_num = blockid + "_input_"+str(k)
        input_node = ASTNode(None, id_num, k, [])
        if k in ["DIRECTION","HEADING","MOTOR","SPIN_DIRECTIONS","NOTE","PORT","COLOR", "CONDITION"]:
            # these reference a separate block
            child_id = v[1]
            if child_id in nodes:
                input_child_node = nodes[child_id]
            else:
                input_child_node = parse_block(child_id, to_parse_queue.pop(child_id), nodes, to_parse_queue)
                input_child_node.parent = input_node
                nodes[child_id] = input_child_node
        else:
            input_child_node = ASTNode(input_node, id_num+"_value", v[1][1], [])
        input_node.children.append(input_child_node)
        node.children.append(input_node)
    return node