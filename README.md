# HardyCross-Solver
 A custom tool for ArcGIS Pro to find the flow values in pipes using Hardy Cross method
 
This tool requires two layers to work on:
- A point layer representing the junctions in the network containing the names and its corresponding flow values. An outflow is denoted by a negative sign.
- A line layer representing the pipes with names as indicated by its direction and its respective k values.

It is required to specify the loop direction of the network for each pipe such that the pipes that allows water to flow in clockwise direction should be given a value of 1 and for counter-clockwise direction, it should be given a value of -1

This tool takes additional parameters like flow exponent value(x), convergence threshold, and total number of iterations to perform.

A sample network along with the toolbox is given in the "HardyCross.gdb" file for reference
