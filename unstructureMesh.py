import random
import numpy as np

class Node:
    def __init__(self, Nid:np.int32, pos:np.array, solidSet:set=set(),halfFace=None) -> None:
        self.Nid = Nid
        self.pos = pos.astype(np.float32)
        # self.solidSet = solidSet
        self.halfFace = halfFace


class HalfFace:
    def __init__(self, Hid:np.int32, solid=None, next=None, pair=None, nodeSet:set=set()) -> None:
        self.Hid = Hid
        self.next = next
        self.pair = pair
        self.solid = solid
        self.nodeSet = nodeSet


class Face:
    def __init__(self, Fid:np.int32, halfFace:HalfFace=None) -> None:
        self.Fid = Fid
        self.halfFace = halfFace


class Solid:
    def __init__(self, Sid, halfFace:HalfFace=None) -> None:
        self.Sid = Sid
        self.halfFace = halfFace

    def get_nodes(self) -> set:
        return self.halfFace.nodeSet | self.halfFace.next.nodeSet  # 时间复杂度 O(len(set))
        

def make_face(prev:HalfFace, nodes:list, FaceDict:dict, Fid:list, solid:Solid):
    order = nodes
    order.sort()
    order = tuple(order)
    
    if order not in FaceDict:
        Hid = Fid[0]*2
        halfFace = HalfFace(Hid=Hid, solid=solid, next=None, pair=None, nodeSet=set(nodes))
        face = Face(Fid=Fid[0], halfFace=halfFace)
        Fid[0] += 1
        FaceDict[order] = face
        if prev: prev.next=halfFace
        return halfFace
    else:
        face = FaceDict[order]
        halfFace = face.halfFace
        if halfFace.solid != solid:
            Hid = face.Fid*2+1   # equal halfFace.Hid+1
            h = HalfFace(Hid=Hid, solid=solid, next=None, pair=halfFace, nodeSet=set(nodes))
            if prev: prev.next=h
            halfFace.pair = h
            return h
        else: return halfFace


def read_msh_file(filename):
    nodeDict = {}
    faceDict = {}
    FaceDict = {}
    with open(filename,'r') as f:
        # 找Node
        s = f.readline()
        while s:
            s = s.rstrip('\n')
            if s == "$Nodes": break
            s = f.readline()
        
        # 读Node
        s = f.readline()
        s = s.rstrip('\n')
        node_num = int(s)
        s = f.readline()
        while s:
            s = s.rstrip('\n')
            if s == "$EndNodes": break
            id,x,y,z = s.split('\t')
            node = Node(np.int32(id),np.array([np.float32(x), np.float32(y), np.float32(z)]), solidSet=set())
            nodeDict[np.int32(id)] = node
            s = f.readline()
        
        # 找Elements
        while s:
            s = s.rstrip('\n')
            if s == "$Elements": break
            s = f.readline()

        # 读Elements
        s = f.readline()
        s = s.rstrip('\n')
        elements_num = int(s)
        s = f.readline()
        Fid = [np.int32(0)]
        while s:
            s = s.rstrip('\n')
            if s == "$EndElements": break
            ssplit = s.split('\t')
            if ssplit[1] == '2':
                id,etype,_,_,_,p1,p2,p3 = ssplit
                faceDict[int(id)] = {int(p1),int(p2),int(p3)}
            elif ssplit[1] == '4':
                Sid,etype,_,_,_,p1,p2,p3,p4 = ssplit
                Sid,p1,p2,p3,p4 = np.int32(Sid), np.int32(p1), np.int32(p2), np.int32(p3), np.int32(p4)
                h1 = make_face(None, [p1,p2,p3], FaceDict, Fid, solid=None)
                solid = Solid(Sid,halfFace=h1)
                h1.solid = solid
                h2 = make_face(h1, [p2,p3,p4], FaceDict, Fid, solid=solid)
                h3 = make_face(h2, [p3,p4,p1], FaceDict, Fid, solid=solid)
                h4 = make_face(h3, [p4,p1,p2], FaceDict, Fid, solid=solid)
                h4.next = h1
                # nodeDict[p1].solidSet.add(solid)
                # nodeDict[p2].solidSet.add(solid)
                # nodeDict[p3].solidSet.add(solid)
                # nodeDict[p4].solidSet.add(solid)
                if nodeDict[p1].halfFace==None: nodeDict[p1].halfFace = h1 
                if nodeDict[p2].halfFace==None: nodeDict[p2].halfFace = h2
                if nodeDict[p3].halfFace==None: nodeDict[p3].halfFace = h3
                if nodeDict[p4].halfFace==None: nodeDict[p4].halfFace = h4
            s = f.readline()
    print("构造完成")
    return nodeDict, faceDict, FaceDict


def search_face(FaceDict:dict, nodes:list) -> Face:
    nodes.sort()
    return FaceDict[tuple(nodes)]


def search_face_by_ID(FaceDict:dict, halfFaceDict:dict, Fid:np.int32) -> Face:
    Hid = Fid*2
    nodes = list(halfFaceDict[Hid].nodeSet)
    nodes.sort()
    return FaceDict[nodes]


def is_boundary(face:Face) -> bool:
    halfFace = face.halfFace
    return halfFace.pair == None


def face_neibor_solid(face:Face) -> set:
    halfFace = face.halfFace
    if is_boundary(face): return {halfFace.solid}
    else: return {halfFace.solid, halfFace.pair.solid}


def search_solid_by_node(node:Node) -> set:
    # return set(),node.solidSet
    halfFace = node.halfFace
    queue = [halfFace]
    visitSet = {halfFace}
    solidSet = {halfFace.solid}
    while len(queue) != 0:
        halfFace = queue.pop(0)
        solidSet.add(halfFace.solid)
        h = halfFace
        while True:
            if (h.pair!=None) and (h.pair not in visitSet) and (node.Nid in h.nodeSet): 
                queue.append(h.pair)
            visitSet.add(h)
            h = h.next
            if h==halfFace: break
    # return solidSet, node.solidSet
    return solidSet
        

def get_face_by_solid(FaceDict:dict, solid:Solid) -> set:
    faceSet = set()
    halfFace = solid.halfFace
    while len(faceSet) < 4:
        nodes = halfFace.nodeSet
        nodes = list(nodes)
        face = search_face(FaceDict, nodes)
        faceSet.add(face)
        halfFace = halfFace.next    
    return faceSet


def solid_neibor_solid(FaceDict:dict, solid:Solid) -> set:
    solidSet = set()
    faceSet = get_face_by_solid(FaceDict, solid)
    for face in faceSet:
        halfFace = face.halfFace
        if halfFace.solid == solid and not is_boundary(face):
            solidSet.add(halfFace.pair.solid)
        elif halfFace.solid != solid: solidSet.add(halfFace.solid)
    return solidSet


def get_solid_by_nodes(FaceDict:dict, fourNotes) -> Solid:
    A,B,C,D = fourNotes
    order = [A,B,C]
    order.sort()
    face = FaceDict[order]
    halfFace = face.halfFace
    if halfFace.solid.get_nodes() == set(fourNotes): return halfFace.solid
    else: return halfFace.pair.solid


if __name__ == "__main__":
    filename = 'uni_tet_x0.1y0.1z0.1.msh'
    nodeDict, faceDict, FaceDict = read_msh_file(filename)

    lst = list(FaceDict)
    random_nodes = random.choice(lst)
    face = search_face(FaceDict, list(random_nodes))
    print(f"选择节点{random_nodes}, 找到编号为{face.Fid}的面")
    print(f"这个面是否为边界:{is_boundary(face)}")
    solid_set = face_neibor_solid(face)
    print(f"这个面相邻的体单元为:"+','.join(str(s.Sid) for s in solid_set))
    print()
    del solid_set

    nodes = list(nodeDict)
    random_node = nodeDict[random.choice(nodes)]
    print(f"选择节点{random_node.Nid}")
    solid_set = search_solid_by_node(random_node)
    print(f"这个节点相邻的体单元为:"+','.join(str(s.Sid) for s in solid_set))
    print(f"与这个节点相邻的体单元个数为{len(solid_set)}")
    print()
    del solid_set

    solid = face.halfFace.solid
    print(f"选择编号为{solid.Sid}的体单元")
    face_set = get_face_by_solid(FaceDict, solid)
    print("这个体单元的面单元编号为:"+','.join(str(f.Fid) for f in face_set))
    solid_set = solid_neibor_solid(FaceDict, solid)
    print("与这个体单元相邻的体单元编号为:"+','.join(str(s.Sid) for s in solid_set))
    print()

    # flag = True
    # for k,v in faceDict.items():
    #     face = search_face(FaceDict,list(v))
    #     if not is_boundary(face):
    #         print("faceDict中的面不一定都是边界")
    #         flag = False
    #         break
    # if flag: print("faceDict中的面都是边界")

    # boundary_face = set()
    # for k,face in FaceDict.items():
    #     if is_boundary(face): boundary_face.add(face)
    # print("所有边界都在faceDict中:",len(boundary_face)==len(faceDict))
