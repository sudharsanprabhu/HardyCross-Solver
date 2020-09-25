# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 11:25:25 2020

@author: S. R. Sudharsan Prabhu
"""

import networkx as nx
import copy
import arcpy


net=nx.DiGraph()
temp=[]
nodesOfLoops=[]
commonNodes=[]
commonEdgeDirection={}
commonEdges=list("")
iterations=0

#Get parameters
featureJunction=arcpy.GetParameterAsText(0)
JunctionName=fieldFlow=arcpy.GetParameterAsText(1)
JunctionFlow=arcpy.GetParameterAsText(2)

featurePipe=arcpy.GetParameterAsText(3)
PipeName=arcpy.GetParameterAsText(4)
PipeLoopDirection=arcpy.GetParameterAsText(5)
PipeK=arcpy.GetParameterAsText(6)

x=float(arcpy.GetParameterAsText(7))
threshold=float(arcpy.GetParameterAsText(8))
totalIterations=float(arcpy.GetParameterAsText(9))


#Define Inputs
inputName=[]
inputK=[]
inputLoopDirection=[]
inputFlow={}

#Assign Inputs
cursor=arcpy.da.SearchCursor(featureJunction,[JunctionName,JunctionFlow])
for row in cursor:
    inputFlow[row[0]]=row[1]

cursor=arcpy.da.SearchCursor(featurePipe,[PipeName, PipeLoopDirection, PipeK])
for row in cursor:
    inputName.append(row[0])
    inputLoopDirection.append(row[1])
    inputK.append(row[2])



#Check input data integrity
for i in inputName:
    if len(i)>2:
        arcpy.AddError("Invalid pipe names... pipe names should be 2 characters only")

for i in inputK:
    if  isinstance(i, str):
        arcpy.AddError("Invalid k value... k value shoud be a number only")

for i in inputLoopDirection:
    if i!=1 and i!=-1:
        arcpy.AddError("Invalid loop direction... Loop direction must be denoted either as 1 or -1 for clockwise and counter clockwise direction")

flowSum=0
for i in inputFlow:
    flowSum+=inputFlow.get(i)
if flowSum!=0:
    arcpy.AddError("Invalid in or out - flow values.. The sum of inflow and outflow should be 0")


#Fill k values
K={}
for i in range(len(inputName)):
    K[inputName[i]]=inputK[i]


#Create graph using edges
for i in range(len(inputName)):
    temp.append(list(inputName[i]))
    net.add_edge(temp[i][0],temp[i][1])


#Fill ungiven flow values as 0
for i in net.nodes:
    if i not in inputFlow:
        inputFlow[i]=0


#Assume flow values
flow={}
for i in inputFlow:
    tempFlow=[]
    for j in inputName:
        if i in j[0]:
            tempFlow.append(j)
    
    for k in tempFlow:
            flow[k]=inputFlow.get(i)/len(tempFlow)
            inputFlow[k[1]]+=flow[k]
            

#Give flow direction
tempflow=copy.deepcopy(flow)
del flow
flow={}
for i in inputName:
   flow[i]=tempflow.get(i)
del tempflow

for i,j in zip(flow,inputLoopDirection):
    flow[i]*=j

"""
Temporary flow values

flow['AB']=25
flow['BD']=25
flow['BC']=50
flow['DC']=-25
flow['AD']=-25
"""



#Find the nodes that forms loops
loops=nx.cycle_basis(net.to_undirected(),root=inputName[0][0])


#Combine individual nodes of a loop
for i in range(len(loops)):
    nodesOfLoops.append("".join(loops[i]))

#Find common edges
for i in range(len(nodesOfLoops)):
    for j in range(i+1,len(nodesOfLoops)):
        comEdg=set(nodesOfLoops[i]) & set(nodesOfLoops[j])
        if(len(comEdg)==2):
            commonEdges.append("".join(comEdg))


#Eliminate edges with more than 2 nodes (Irrelevant edges) and repeating edges
for i in commonEdges:
    if commonEdges.count(i)>1:
        commonEdges.remove(i)


#Verify if the edges are named according to its direction as given. Else correct it
def checkName(edgeList, defaultEdgeList):
    if isinstance(edgeList, list):    
        for i in range(len(edgeList)):
            if(edgeList[i]) not in defaultEdgeList:
                edgeList[i]=edgeList[i][::-1]
    
    elif isinstance(edgeList, str):
        if edgeList not in defaultEdgeList:
            edgeList=edgeList[::-1]
    return edgeList

commonEdges=checkName(commonEdges, inputName)


#Extend nodesOfLoops to insert attributes
for i in range(len(nodesOfLoops)):
    nodesOfLoops[i]=[nodesOfLoops[i]]

loopEdges = copy.deepcopy(nodesOfLoops)
loopCommonEdges = copy.deepcopy(nodesOfLoops)


#Associate edges with loops
for i in range(0,len(nodesOfLoops)):
    for j in inputName:
        edge=set(nodesOfLoops[i][0]) & set(j)
        if(len(edge)==2):
            edge=checkName("".join(edge), inputName)
            loopEdges[i].append("".join(edge))


#Associate common edges with loops
for i in range(0,len(nodesOfLoops)):
    for j in commonEdges:
        edge=set(nodesOfLoops[i][0]) & set(j)
        if(len(edge)==2):
            edge=checkName("".join(edge), inputName)
            loopCommonEdges[i].append("".join(edge))

#print(loopEdges)
#print(loopCommonEdges)


            

while True:

    hl=[]
    sumOfhl=[]
    hlQa=[]
    sumOfhlQa=[]
    delta={}
    commonDelta={}
    stopIteration=True

    
#Find HL
    for i in range(len(loopEdges)):
        hl.append([])
        for j in range(1,len(loopEdges[i])):
            if i>0 and loopEdges[i][j] in loopCommonEdges[i]:
                commonLoopDirection=-1
            else:
                commonLoopDirection=1
        
            if flow[loopEdges[i][j]]<0:
                hl[i].append(K[loopEdges[i][j]]*(-1*flow[loopEdges[i][j]]**x)*commonLoopDirection)
            else:
                hl[i].append(K[loopEdges[i][j]]*(flow[loopEdges[i][j]]**x)*commonLoopDirection)

#Find Hl/Qa
    for i in range(len(loopEdges)):
        hlQa.append([])
        for j in range(1,len(loopEdges[i])):
            hlQa[i].append(abs(hl[i][j-1]/flow[loopEdges[i][j]]))
    

#Find sum of hl
    for i in range(len(hl)):
        sumOfhl.append(sum(hl[i]))

#Find sum of Hl/Qa
    for i in range(len(hlQa)):
        sumOfhlQa.append(sum(hlQa[i]))


#Find delta correction
    for i in range(len(loopEdges)):
        delta[loopEdges[i][0]]=-1*sumOfhl[i]/(x*sumOfhlQa[i])


#Apply Correction
    for i in range(len(loopEdges)):
        for j in range(1,len(loopEdges[i])):
            if loopEdges[i][j] not in loopCommonEdges[i]:
                flow[loopEdges[i][j]]+=delta[loopEdges[i][0]]
            else:
                if loopEdges[i][j] not in commonDelta:
                    commonDelta[loopEdges[i][j]]=delta[loopEdges[i][0]]
                else:
                    commonDelta[loopEdges[i][j]]=commonDelta[loopEdges[i][j]]-delta[loopEdges[i][0]]


#Apply correction for common edges:
    temp=[] #Correction to be applied to a common edge only once

    for i in range(len(loopEdges)):
        for j in range(1,len(loopEdges[i])):
            if loopEdges[i][j]  in loopCommonEdges[i] and loopEdges[i][j] not in temp:
                flow[loopEdges[i][j]]+=commonDelta[loopEdges[i][j]]
                temp.append(loopEdges[i][j])
    
    iterations+=1     
    
    #Compute whether required threshold is attained or not
    for i in delta:
        if abs(delta[i]) > threshold:
            stopIteration=False
   
    #print average delta value for each interation
    tempDeltaValues=[]
    for tempDelta in delta.values():
        tempDeltaValues.append(abs(tempDelta))
    arcpy.AddMessage("Average correction after iteration "+str(iterations)+" :"+str(sum(tempDeltaValues)/len(tempDeltaValues)))

	
    #Iteration conditions
    if iterations == totalIterations or stopIteration:
        break


print(flow)


#Fill flow values in atribute table
arcpy.AddField_management(featurePipe,'Flow','DOUBLE')
cursor=arcpy.da.UpdateCursor(featurePipe,[PipeName,'Flow'])
arcpy.AddMessage("Total number of iterations done: "+str(iterations))
for row in cursor:
    row[1]=abs(flow[row[0]])
    cursor.updateRow(row)











