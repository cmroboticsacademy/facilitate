from parsing.ast import ASTNode, OpCodes

def build_ast_tree(program_blocks:dict):
    root_node = None
    nodes = {} # block id: node
    for blockid, block in program_blocks.items():
        parent_id = block["parent"]
        oc = block["opcode"]
        try:
            desc = OpCodes[oc]
        except:
            desc = oc
        child_id = block["next"]
        
        node = ASTNode(None, blockid, desc, [])
        
        if parent_id in nodes:
            node.parent = nodes[parent_id]
            nodes[parent_id].children.append(node)
            
        if child_id in nodes:
            node.children.append(nodes[child_id])
        
        for k, v in block["fields"].items():
            id_num = blockid+"_field_"+str(k)
            field_node = ASTNode(None, id_num, k, [])
            field_child_node = ASTNode(field_node, id_num+"_value", v, [])
            field_node.children.append(field_child_node)
            node.children.append(field_node)
            
        for k, v in block["inputs"].items():
            id_num = blockid+"_input_"+str(k)
            input_node = ASTNode(None, id_num, k, [])
            input_child_node = ASTNode(input_node, id_num+"_value", v, [])
            input_node.children.append(input_child_node)
            node.children.append(input_node)
    
        nodes[blockid] = node
        
        if block["topLevel"] and desc == OpCodes.event_whenprogramstarts:
            root_node = node
    return root_node