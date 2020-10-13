from tmgen.models import modulated_gravity_tm, spike_tm, random_gravity_tm
from tmgen import TrafficMatrix
 
def Get_edges (topo):
    if topo == "B4":
##### B4 topology #####
        edges_list = [(1,2),(1,4),(1,6),(2,3),(3,5),(4,5),(4,7),(4,8),(5,6),(6,7),(6,8),(7,8),(7,9),(8,10),(9,10),(9,11),(9,12),(10,11),(10,12)]
        n = 12
        
    elif topo == "ATT":
##### ATT topology #####
        edges_list = [(1,2),(1,3),(1,7),(1,8),(2,7),(3,4),(3,7),(3,10),(3,16),(3,17),(3,18),(3,21),(3,22),(4,9),(4,10),(4,7),(5,6),(5,8),(6,8),(6,9),(6,10),(6,14),
                  (6,15),(7,8),(9,10),(9,14),(10,14),(10,17),(10,23),(11,12),(11,14),(11,15),(12,13),(12,14),(12,15),(13,25),(13,14),(14,16),(14,17),
                  (14,18),(14,23),(16,17),(16,18),(16,22),(17,18),(18,19),(18,20),(18,21),(18,22),(18,23),(19,22),(20,21),(22,23),(23,24),(23,25),(24,25)]
        n = 25

    elif topo == "Bestel":    
##### Bestel topology #####
        edges_list = [(1,44),(1,45),(2,45),(2,46),(2,72),(3,57),(3,4),(4,54),(5,66),(5,11),(6,66),(6,28),(6,53),(6,26),(7,55),(7,72),(8,30),(8,31),(9,10),(9,76),
                      (10,11),(11,56),(12,61),(12,56),(13,67),(13,60),(14,76),(14,37),(14,56),(15,59),(15,20),(16,59),(16,20),(17,19),(17,64),(18,50),(18,79),
                      (19,22),(19,23),(19,32),(20,33),(20,34),(20,39),(20,60,),(21,49),(21,23),(22,62),(24,26),(24,32),(25,29),(25,32),(27,28),(27,29),(30,76),
                      (31,46),(34,61),(35,82),(35,83),(35,80),(36,41),(36,54),(37,81),(38,61),(38,39),(39,60),(40,41),(41,42),(42,43),(42,44),(47,70),(47,48),(48,79),
                      (49,55),(50,73),(51,71),(51,63),(52,73),(52,68),(53,61),(56,67),(57,84),(58,65),(58,59),(62,70),(63,64),(68,69),(69,70),(69,71),(74,75),
                      (75,79),(77,78),(78,79),(78,80),(78,80)]
        n= 84
        
    elif topo == "Cognet":
##### Cognet topology #####
        edges_list = [(1,177),(1,10),(2,9),(2,177),(2,115),(2,117),(2,176),(3,77),(3,78),(4,5),(4,78),(5,7),(5,136),(6,132),
                      (6,7),(7,8),(8,9),(8,175),(9,195),(9,10),(9,192),(11,12),(11,14),(12,17),(13,33),(13,14),(13,31),(14,17),
                      (14,16),(15,65),(15,130),(15,16),(17,18),(19,20),(19,31),(20,90),(20,69),(20,83),(21,22),(21,24),(22,27),
                      (23,189),(23,24),(25,28),(26,172),(26,56),(27,28),(27,29),(27,30),(29,52),(29,55),(30,79),(31,36),(32,38),
                      (33,34),(33,38),(35,38),(37,39),(37,40),(38,161),(38,39),(39,197),(40,182),(41,42),(41,43),(42,44),(42,190),
                      (43,44),(43,144),(45,46),(45,48),(46,49),(46,165),(47,50),(47,48),(49,156),(49,182),(50,178),(50,166),
                      (51,58),(51,52),(52,189),(53,54),(53,56),(54,59),(55,56),(57,58),(57,60),(59,60),(61,62),(61,70),(62,129),
                      (62,123),(63,145),(63,87),(63,64),(64,69),(64,150),(65,66),(65,68),(65,69),(66,67),(67,68),(68,70),(70,145),
                      (71,80),(71,184),(72,73),(72,80),(73,74),(74,75),(75,184),(76,174),(76,184),(77,174),(78,153),(78,163),(78,134),
                      (79,95),(79,80),(81,82),(81,87),(81,88),(83,89),(83,84),(83,151),(84,149),(85,149),(85,86),(87,88),(88,89),(90,151),
                      (91,173),(92,100),(92,93),(93,97),(93,94),(93,184),(95,172),(96,97),(96,172),(97,98),(98,173),(99,195),(99,132),
                      (100,101),(101,133),(102,105),(102,181),(102,103),(103,110),(104,105),(104,107),(106,107),(106,108),(106,180),
                      (108,109),(108,130),(109,180),(110,111),(111,129),(112,113),(112,141),(113,138),(114,115),(114,192),(116,117),
                      (116,119),(118,121),(118,119),(120,177),(120,176),(121,176),(122,123),(122,125),(124,125),(124,126),(124,127),
                      (128,129),(128,131),(130,131),(132,143),(133,136),(134,174),(135,138),(135,139),(135,136),(137,140),(138,173),
                      (139,175),(139,142),(140,175),(141,142),(143,144),(144,186),(145,150),(146,158),(147,153),(147,155),(148,167),
                      (148,178),(149,155),(150,151),(152,153),(153,154),(154,161),(154,155),(155,160),(155,184),(156,196),(156,157),
                      (156,166),(157,158),(158,159),(159,184),(159,166),(162,163),(163,164),(163,168),(164,188),(164,165),(166,182),
                      (166,185),(166,187),(167,171),(167,184),(168,169),(169,170),(170,186),(179,180),(182,197),(183,190),(184,185),
                      (184,187),(187,188),(191,192),(193,194),(194,195),(196,197)]
        n= 197
        
    elif topo == "Dial_Telecom":
##### Dial Telecom #####
        edges_list = [(2, 116), (2, 172), (3, 5), (3, 172), (3, 165), (5, 6), (7, 172), (7, 8), (11, 12), (11, 32), (12, 90), (20, 85), (20, 86), (21, 27), (21, 24),
         (23, 30),(24, 132), (26, 101), (26, 95), (27, 28), (27, 29), (28, 101), (29, 59), (30, 68), (30, 69), (31, 32), (32, 35), (32, 39), (34, 39), (37, 151),
         (37, 40),(38, 161), (38, 150), (39, 139), (41, 42), (41, 43), (42, 47), (43, 179), (43, 147), (45, 160), (45, 46), (45, 48), (46, 50), (47, 173), (50, 173),
         (51, 57),(51, 52), (51, 184), (54, 170), (54, 59), (57, 60), (56, 59), (58, 170), (60, 170), (61, 169), (62, 169), (62, 123), (63, 81), (63, 65), (63, 89),
         (63, 146),(64, 65), (64, 80), (66, 146), (67, 81), (67, 104), (68, 69), (68, 70), (68, 71), (68, 80), (68, 146), (70, 169), (71, 145), (73, 74), (72, 145),
         (72, 73),(74, 133), (79, 95), (80, 145), (83, 89), (83, 90), (84, 85), (83, 85), (84, 105), (83, 84), (88, 89), (91, 96), (91, 94), (91, 168), (92, 171),
         (92, 168),(94, 171), (95, 96), (98, 168), (99, 153), (99, 144), (102, 152), (104, 111), (105, 110), (107, 109), (107, 168), (109, 110), (111, 171),
         (113, 122),(113, 139), (115, 116), (116, 118), (118, 122), (123, 126), (125, 126), (125, 127), (125, 128), (127, 130), (129, 130), (129, 132), (133, 136),
         (135, 138),(135, 136), (138, 188), (139, 140), (140, 188), (144, 180), (144, 187), (147, 153), (147, 178), (147, 152), (148, 149), (148, 150), (149, 154),
         (150, 174),(151, 174), (154, 155), (152, 193), (152, 153), (153, 154), (156, 157), (156, 174), (157, 160), (159, 165), (161, 162), (162, 166), (164, 165),
         (165, 173),(178, 179), (181, 182), (180, 181), (182, 184), (187, 188), (188, 191), (191, 192), (192, 193)]	
        n = 193 
    return edges_list, n, len(edges_list)*2

def TMGeneration(n):
    tm1 = modulated_gravity_tm(n,1,100)
    tm2 = spike_tm(n,int(n/4),1)
    tm3 = tm3 = random_gravity_tm(n,20)
    print(tm1)
    print("8888888")
    print(tm2)
    print("8888888")
    print(tm3)
    print("8888888")

    flows = {}
    for i in range(1,n+1):
        for j in range(1,n+1):
            if j != i:
                print(i,j)  
                flows[i,j,30] = tm1.matrix[j-1,i-1,0]
                flows[i,j,20] = tm2.matrix[j-1,i-1,0]
                flows[i,j,10] = tm3.matrix[j-1,i-1,0]


    return(flows)




