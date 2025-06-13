import requests
import json
import math
import re
import os

def getAnnotation(relationID):
    neg = ["improbable","impossible"]
    abstrait = ["hypothétique","métaphore"]
    unPeuNeg = ["non spécifique","peu pertinent","subjectif"]
    pos = ["pertinent","vrai"]
    tresPos = ["constitutif","toujours vrai"]

    urlAnno = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/:r{relationID}"
    repAnno = requests.get(urlAnno)
    dataAnno = repAnno.json()

    # Pas d'annotation, on ignore
    if next(iter(dataAnno)) == "error":
        return 1,None

    listeAnno = []
    for anno in dataAnno["nodes"]:
        if anno["name"] != "Relation:" and anno["name"][:1] != ":r":
            listeAnno.append(anno["name"])

    #print(listeAnno)
    res = 1
    for anno in unPeuNeg:
        if anno in listeAnno:
            res *= 0.5
    for anno in abstrait:        
        if anno in listeAnno:
            res *= 0.5
    for anno in neg:
        if anno in listeAnno:
            res *= 0
    for anno in pos:        
        if anno in listeAnno:
            res *= 1.5
    for anno in tresPos:        
        if anno in listeAnno:
            res *= 1.8

    if "contrastif" in listeAnno:
        return res,-1
    else:
        return res,None



def getRaffinement(noeud1,entite,noeud2):
    urlNomRaf = f"https://jdm-api.demo.lirmm.fr/v0/node_by_id/{entite}"
    dataNomRaf = requests.get(urlNomRaf).json()
    nomEntite = dataNomRaf["name"]

    # Si l'entité est déjà un raffinement, ne pas chercher plus loin
    if ">" in nomEntite:
        return True

    # récupérer tous les raffinements de l'entite
    urlRaf = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{nomEntite}?types_ids=1"
    filenameRafEntite = re.sub(r'[^\w\-_]', '_', urlRaf)
    dataRaf = ""
    if not os.path.exists(f"cache/{filenameRafEntite}.json"):
        dataRaf = requests.get(urlRaf).json()
        #print("requete 1 faite")
        with open(f'cache/{filenameRafEntite}.json', 'w', encoding='utf-8') as file:
            json.dump(dataRaf, file, indent=4, ensure_ascii=False)
    else:
        with open(f"cache/{filenameRafEntite}.json", "r", encoding="utf-8") as file:
            dataRaf = json.load(file)

    # si l'entité du milieu n'a pas de raffinement, c'est forcement la meme entité partout
    if next(iter(dataRaf)) == "error":
        return True
    
    for node in dataRaf["nodes"]:
        if node["name"] != nomEntite:
            raffinement = node["name"]

            urlN1EFull = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud1}/to/{raffinement}?wight>0"
            repN1EFull = requests.get(urlN1EFull)
            urlEN2Full = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{raffinement}/to/{noeud2}?weight>0"
            repEN2Full = requests.get(urlEN2Full)

            dataN1E = repN1EFull.json()
            dataEN2 = repEN2Full.json()

            if next(iter(dataN1E)) != "error" and next(iter(dataEN2)) != "error" and len(dataN1E["relations"]) != 0 and len(dataEN2["relations"]) != 0:
                return True
    return False



def synonyme(noeud1, noeud2, relationName):
    
    relationNum = numsRelations.get(relationName)

    # récuérer tous les synonymes de noeud1
    urlGenNoeud1 = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud1}?types_ids=5&min_weight=1"
    # récupérer tous les noeuds allant vers noeud2 avec la relation relationNum
    urlRToNoeud2 = f"https://jdm-api.demo.lirmm.fr/v0/relations/to/{noeud2}?types_ids={relationNum}&min_weight=1"

    filenameUrl1 = re.sub(r'[^\w\-_]', '_', urlGenNoeud1)
    filenameUrl2 = re.sub(r'[^\w\-_]', '_', urlRToNoeud2)

    dataGenN1 = ""
    dataRN2 = ""
    if not os.path.exists(f"cache/{filenameUrl1}.json"):
        repGenN1 = requests.get(urlGenNoeud1)
        #print("requete 1 faite")
        if repGenN1.status_code == 200:
            dataGenN1 = repGenN1.json()
            with open(f'cache/{filenameUrl1}.json', 'w', encoding='utf-8') as file:
                json.dump(dataGenN1, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repGenN1.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl1}.json", "r", encoding="utf-8") as file:
            dataGenN1 = json.load(file)
        #print("chargement 1 fait")


    if not os.path.exists(f"cache/{filenameUrl2}.json"):
        repRToNoeud2 = requests.get(urlRToNoeud2)
        if repRToNoeud2.status_code == 200:
            dataRN2 = repRToNoeud2.json()
            #print("requete 2 faite")
            with open(f'cache/{filenameUrl2}.json', 'w', encoding='utf-8') as file:
                json.dump(dataRN2, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repRToNoeud2.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl2}.json", "r", encoding="utf-8") as file:
            dataRN2 = json.load(file)
        #print("chargement 2 fait")


    if len(dataGenN1["relations"]) == 0:
        print(f"Non, pas selon JDM || {noeud1} n'a pas de synonyme")
        return 0

    if len(dataRN2["relations"]) == 0:
        print(f"Non, pas selon JDM || il n'y a pas de relation de type {relationNum} vers {noeud2}")
        return 0
    
    # Enlever les noeuds qui commencent pas "en:" ou qui sont raffinés et les relations liées
    noeudsAnglaisRaf = {node["id"] for node in dataGenN1["nodes"] if node["name"].startswith("en:") or ">" in node["name"]}
    dataGenN1["nodes"] = [node for node in dataGenN1["nodes"] if node["id"] not in noeudsAnglaisRaf]
    dataGenN1["relations"] = [rel for rel in dataGenN1["relations"] if rel["node2"] not in noeudsAnglaisRaf]

    maxW = 0
    for relationBrute in dataGenN1["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normRelationsGen = dataGenN1["relations"]
    for rel in normRelationsGen:
        rel["w"] = rel["w"]/maxW

    maxW = 0
    for relationBrute in dataRN2["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normRelationsR = dataRN2["relations"]
    for rel in normRelationsR:
        rel["w"] = rel["w"]/maxW


    # Récupérer les IDs et les poids des relations des noeuds relatifs aux relations
    entiteGenIDList = {}
    entiteAgentIDList = {}
    # noeud1 - R_syn - {noeud2}
    for relation in normRelationsGen:
        entiteGenIDList[relation["node2"]] = [relation["w"],relation["id"]]
    # {noeud1} - relationName - noeud2
    for relation in normRelationsR:
        entiteAgentIDList[relation["node1"]] = [relation["w"],relation["id"]]

    # Intersection et moyenne géométrique
    intersectionIDs = {}
    for val in entiteGenIDList.keys():
        if val in entiteAgentIDList.keys():
            # FAIRE UNE UPDATE PAR ANNOTATION avec l'id de la relation
            resAnnoN1Gen,contrasN1Gen = getAnnotation(entiteGenIDList.get(val)[1])
            resAnnoGenN2,contrasGenN2 = getAnnotation(entiteAgentIDList.get(val)[1])
            resAnnoN1Gen = float(resAnnoN1Gen)
            resAnnoGenN2 = float(resAnnoGenN2)

            if contrasN1Gen != None or contrasGenN2 != None:
                # Si Contrastif : FAIRE UNE VERIF DE RAFFINEMENT
                if (getRaffinement(noeud1,val,noeud2)):
                    if contrasN1Gen != None and resAnnoN1Gen > 1:
                        resAnnoN1Gen = 1.8
                    if contrasGenN2 != None and resAnnoGenN2 > 1:
                        resAnnoGenN2 = 1.8
            intersectionIDs[val] = math.sqrt((entiteGenIDList[val][0]*resAnnoN1Gen) * (entiteAgentIDList[val][0]*resAnnoGenN2))
             
    sortedIntersectionIDs = dict(sorted(intersectionIDs.items(), key=lambda item: item[1], reverse=True))


    if not intersectionIDs:
        print(f"Non || Aucune intersection entre les synonymes de {noeud1} et les noeuds ayant une relation de type {relationName} vers {noeud2}")
        return 0

    # Affichage du résultat
    i=1
    for idNoeud in sortedIntersectionIDs.keys(): 
        for noeud in dataGenN1["nodes"]:
            if noeud["id"] == idNoeud:
                print(f"{i} || oui || {noeud1} -r_syn-> {noeud["name"]}  >  {noeud["name"]} -{relationName}-> {noeud2} || poids = {intersectionIDs[idNoeud]}")
                i+=1
        if i > 10:
            break

    return 0



#-------




def synonymeCarre(noeud1, noeud2, relationName):
    
    relationNum = numsRelations.get(relationName)

    # récuérer tous les synonymes de noeud1 et noeud2
    urlSynNoeud1 = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud1}?types_ids=5&min_weight=1"
    urlSynNoeud2 = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{noeud2}?types_ids=5&min_weight=1"
    
    filenameUrl1 = re.sub(r'[^\w\-_]', '_', urlSynNoeud1)
    filenameUrl2 = re.sub(r'[^\w\-_]', '_', urlSynNoeud2)

    dataSynN1 = ""
    dataSynN2 = ""
    if not os.path.exists(f"cache/{filenameUrl1}.json"):
        repSynN1 = requests.get(urlSynNoeud1)
        #print("requete 1 faite")
        if repSynN1.status_code == 200:
            dataSynN1 = repSynN1.json()
            with open(f'cache/{filenameUrl1}.json', 'w', encoding='utf-8') as file:
                json.dump(dataSynN1, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repSynN1.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl1}.json", "r", encoding="utf-8") as file:
            dataSynN1 = json.load(file)
        #print("chargement 1 fait")


    if not os.path.exists(f"cache/{filenameUrl2}.json"):
        repSynN2 = requests.get(urlSynNoeud2)
        if repSynN2.status_code == 200:
            dataSynN2 = repSynN2.json()
            #print("requete 2 faite")
            with open(f'cache/{filenameUrl2}.json', 'w', encoding='utf-8') as file:
                json.dump(dataSynN2, file, indent=4, ensure_ascii=False)
        else:
            print(f"Erreur {repSynN2.status_code}: Impossible d'accéder au fichier JSON")
    else:
        with open(f"cache/{filenameUrl2}.json", "r", encoding="utf-8") as file:
            dataSynN2 = json.load(file)
        #print("chargement 2 fait")


    if len(dataSynN1["relations"]) == 0:
        print(f"Non, pas selon JDM || {noeud1} n'a pas de synonyme")
        return 0

    if len(dataSynN2["relations"]) == 0:
        print(f"Non, pas selon JDM || il n'y a pas de relation de type {relationNum} vers {noeud2}")
        return 0
    
    # Enlever les noeuds qui commencent pas "en:" ou qui sont raffinés et les relations liées
    noeudsAnglaisRaf = {node["id"] for node in dataSynN1["nodes"] if node["name"].startswith("en:") or ">" in node["name"]}
    dataSynN1["nodes"] = [node for node in dataSynN1["nodes"] if node["id"] not in noeudsAnglaisRaf]
    dataSynN1["relations"] = [rel for rel in dataSynN1["relations"] if rel["node2"] not in noeudsAnglaisRaf]

    maxW = 0
    for relationBrute in dataSynN1["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normSynN1 = dataSynN1["relations"]
    for rel in normSynN1:
        rel["w"] = rel["w"]/maxW

    maxW = 0
    for relationBrute in dataSynN2["relations"]:
        if relationBrute["w"] > maxW:
            maxW = relationBrute["w"]
    normSynN2 = dataSynN2["relations"]
    for rel in normSynN2:
        rel["w"] = rel["w"]/maxW

    print("début des recherches syn")

    # Récupérer les IDs et les poids des relations des noeuds relatifs aux relations
    entiteSynN1List = {}
    entiteSynN2List = {}
    # noeud1 - R_syn - {noeudSyn}
    for relation in normSynN1:
        syn = relation["node2"]
        for noeud in dataSynN1["nodes"]:
            if noeud["id"] == syn:
                syn = noeud["name"]
        entiteSynN1List[relation["node2"]] = [relation["w"],relation["id"],syn]
    # noeud2 - R_syn - {noeudSyn}
    for relation in normSynN2:
        syn = relation["node2"]
        for noeud in dataSynN2["nodes"]:
            if noeud["id"] == syn:
                syn = noeud["name"]
        entiteSynN2List[relation["node2"]] = [relation["w"],relation["id"],syn]

    print("maj poids syn")
    # Mise à jour des poids des relations r_syn par annotations et raffinements
    for syn in entiteSynN1List.keys():
        resAnnoN1,_ = getAnnotation(entiteSynN1List.get(syn)[1])
        entiteSynN1List[syn][0] = entiteSynN1List[syn][0]*resAnnoN1

    for syn in entiteSynN2List.keys():
        resAnnoN2,_ = getAnnotation(entiteSynN2List.get(syn)[1])
        entiteSynN2List[syn][0] = entiteSynN2List[syn][0]*resAnnoN2

    print("recherche lien entre syns")
    # Intersection et moyenne géométrique
    relationsIDs = {}
    print(len(entiteSynN1List.keys()))
    print(len(entiteSynN2List.keys()))
    for syn1 in entiteSynN1List.keys():
        for syn2 in entiteSynN2List.keys():
            urlSyn1ToSyn2 = f"https://jdm-api.demo.lirmm.fr/v0/relations/from/{entiteSynN1List[syn1][2]}/to/{entiteSynN2List[syn2][2]}?types_ids={relationNum}&min_weight=1"
            repSyn1ToSyn2 = requests.get(urlSyn1ToSyn2)
            dataSyn1ToSyn2 = repSyn1ToSyn2.json()

            if len(dataSyn1ToSyn2["relations"]) != 0:
                idRel = dataSyn1ToSyn2["relations"][0]["id"]
                # FAIRE UNE UPDATE PAR ANNOTATION avec l'id de la relation
                resAnnoSyn1ToSyn2,_ = getAnnotation(idRel)
                resAnnoSyn1ToSyn2 = float(resAnnoSyn1ToSyn2)

                relationsIDs[idRel] = [math.sqrt(entiteSynN1List[syn1][0] * entiteSynN2List[syn2][0] * (dataSyn1ToSyn2["relations"][0]["w"]*resAnnoSyn1ToSyn2)), entiteSynN1List[syn1][2], entiteSynN2List[syn2][2]]
             
    print("sort")
    sortedRelationsIDs = dict(sorted(relationsIDs.items(), key=lambda item: item[0], reverse=True))


    if not sortedRelationsIDs:
        print(f"Non || Aucun synonymes de {noeud1} et synonyme de {noeud2} ne sont liés par une relation de type {relationName}")
        return 0

    # Affichage du résultat
    i=1
    for idRelation in sortedRelationsIDs.keys(): 
        print(f"{i} || oui || {noeud1} -r_syn-> {syn1}  +  {noeud2} -r_syn-> {syn2} > {syn1} -{relationName}-> {syn2} || poids = {sortedRelationsIDs[idRelation][0]}")
        i+=1
        if i > 10:
            break

    return 0

    




numsRelations = {"r_isa" : 6 ,
                "r_agent-1" : 24,
                "r_lieu" : 15,
                "r_carac" : 17,
                "r_patient" : 14,
                "r_hypo" : 8,
                "r_holo" : 10}


#SYNONYME TRIANGLE
# Résponse = OUI
synonyme("serveuse","apporter à boire","r_agent-1")

# Pas de synonyme
#synonyme("Airbus A380","attérir","r_agent-1")

#synonyme("avocat","pousser","r_agent-1")
#synonyme("tigre","chasser","r_agent-1")
#synonyme("pigeon","voler","r_agent-1")
#synonyme("pigeon","pondre","r_agent-1")
#synonyme("Tour Eiffel","France","r_lieu")
#synonyme("tigre","dangereux","r_carac")
#synonyme("chat","miauler","r_agent-1")
#synonyme("piston","voiture","r_holo")
#synonyme("couper","poulet","r_patient")
#synonyme("couper","pain","r_patient")


#SYNONYME CARRÉ (très long)
#synonymeCarre("couper","pain","r_patient")
