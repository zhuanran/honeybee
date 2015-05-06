# Need a check so that only data from Honeybee_Read_Honeybee_generation_system_results can be connected at one time!!

"""
Use this component to the calculate and visualise the financial value of Honeybee generation systems.
-
Provided by Ladybug 0.0.59
    
    Args:
        _inputData: To use this component please input all the outputs from the component readEP_generation_system_results here
        discount_factor: An optional input - specify the interest rate as a percentage to calculate a discount factor for each Honeybee generation system. A discount factor is a ratio used to calculate the present value of a future revenue or cost that occurs in any year of the system lifetime (25 years) using the equation - fd = 1/(1+i)^N where: i = real interest rate ,N = number of years. If this field is left blank no discount factor will be applied
        gridelect_cost_schedule: The cost of grid connected electricty per Kwh in whatever currency the user wishes - (Just make it consistent with other components you are using)
        If you want to specify a flat rate just specify one value this will be used across all the hours of the year.
        Otherwise specify the grid electricity cost for 288 hours of the year that is for each hour of the day for one day in every month of the year.
        Use a list with 288 values to do this.
        feedin_tariff_schedule: The price that the utility will pay per Kwh in whatever currency the user wishes - (Just make it consistent with other components you are using) for power fed back into the grid. 
        If you want to specify a flat rate just specify one value this will be used across all the hours of the year.
        Otherwise specify the grid electricity cost for 288 hours of the year that is for each hour of the day for one day in every month of the year.
        Use a list with 288 values to do this.
        currency: The currency of the financial data, enter either the symbol or a sentence describing the currency e.g - US dollars
        graph_data: Set to True to visualise the the financial value of Honeybee generation systems.
        _basePoint_: An optional point with which to locate the 3D chart in the Rhino Model.  The default is set to the Rhino origin at (0,0,0).

    Returns:
        readMe!: ...
        gensystem_value: The net present cost of each Honeybee generation system. The net present cost is the present value of all the costs of installing and operating that Honeybee generation system over 25 years minus the present value of the all the revenues that the system earns over 25 years. 
        Thus a positive value means that compared to just buying electricity from the grid the Honeybee generation system will save money while a negative value means that it will be more cost effective to simply buy electricity from the grid.
        graphMesh: A 3D plot of the input data as a colored mesh.  Multiple meshes will be output for several input data streams or graph scales.
        graphCurves: A list of curves and test surfaces representing the time periods corresponding to the input data.  Note that if the time period of the input data is not clear, no curves will be generated here.
        legend: A legend of the chart. Connect this output to a grasshopper "Geo" component in order to preview the legend in the Rhino scene.
        legendBasePts: The legend base point, which can be used to move the legend in relation to the chart with the grasshopper "move" component.
        titleText: String values representing the title and time labels of the chart.  Hook this up to a Ladybug "TextTag3D" component in order to get text that bakes into Rhino as text.
        titleBasePts: Points for placement of the title and time labels of the chart.  Hook this up to a Ladybug "TextTag3D" component in order to get text that bakes into Rhino as text.
        conditionalHOY: The input data for the hours of the year that pass the conditional statement.
"""


from System import Object
import Grasshopper.Kernel as gh
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import scriptcontext as sc
import Rhino as rc
import itertools
import System

lb_visualization = sc.sticky["ladybug_ResultVisualization"]()

ghenv.Component.Name = "Honeybee_Visualise_Honeybeegeneration_cashflow"
ghenv.Component.NickName = 'Visualise_Honeybee_generation_cashflow'
ghenv.Component.Message = 'VER 0.0.56\nMay_06_2015'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "09 | Energy | Energy"
#compatibleHBVersion = VER 0.0.56\nFEB_01_2015
#compatibleLBVersion = VER 0.0.59\nFEB_01_2015
ghenv.Component.AdditionalHelpFromDocStrings = "0"

def stringtoFloat(sequence):
    # stringtoFloat converts items in list from strings to floats, if not possible it removes the item from the list
    # Initialise empty floats array
    floats = []
    # Loop through each string in the input
    for string in sequence: 
        # If the string converts to a float, put it in the floats list.
        try:
            myFloat = float(string)
            floats.append(myFloat)
        # Otherwise pass
        except: 
            pass
    # return the list of floats
    return floats
   

def checkforhoneybeegeneration(_inputData):
    
    """ This function extracts each set of data from the input to the component - _inputData
    (e.g - "Whole Building:Facility Net Purchased Electric Energy" is one set of data)
    and checks that..
    
    1. The EnergyPlus simulation that produced the data was run over an annual period
    2. All the different data sets were run over the same period
    
    If the data passes the conditions above, then the length of each dataset is returned (Only one length is returned
    as all the datasets are the same) this is then used to extract specific datasets from the entire _inputData
    
    """
    
    # Create a list which contains the starting position (columncount) of each set of data 
    # e.g - "Whole Building:Facility Net Purchased Electric Energy" is one set of data
    # Using this we can determine whether the runtime of each set of data is the same.
    runtime = [] 
    # Create a list of the starting position of each set of data and the name of that data
    # e.g - "Whole Building:Facility Net Purchased Electric Energy" is one set of data
    # return this list from this function if the data passes all the checks in this function.
    runtimeandname = []
    
    for columncount,column in enumerate(_inputData):
        
        if isinstance(column, basestring) == True:
            
            if "Whole Building:Facility Net Purchased Electric Energy" in column:
                
                runperiodstart = _inputData[columncount+3]
                runperiodstartend = _inputData[columncount+4]
                
                runtime.append(columncount)
                
                # Check that the runperiod is annual this is necessary to create the cost graph
                
                if (runperiodstart[0] != 1) or (runperiodstart[1] != 1) or (runperiodstart[2] != 1):
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                if (runperiodstartend[0] != 12) or (runperiodstartend[1] != 31) or (runperiodstartend[2] != 24):
                    
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                runtimeandname.append((columncount,'Whole Building:Facility Net Purchased Electric Energy'))
                    
            if 'Whole Building:Facility Total Electric Demand Power' in column:
                
                runperiodstart = _inputData[columncount+3]
                runperiodstartend = _inputData[columncount+4]
                
                runtime.append(columncount)
                
                # Check that the runperiod is annual this is necessary to create the cost graph
                
                if (runperiodstart[0] != 1) or (runperiodstart[1] != 1) or (runperiodstart[2] != 1):
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                if (runperiodstartend[0] != 12) or (runperiodstartend[1] != 31) or (runperiodstartend[2] != 24):
                    
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                runtimeandname.append((columncount,'Whole Building:Facility Total Electric Demand Power'))
                
            if column.find('Electric energy produced by the generator system named - ') != -1:
                
                runperiodstart = _inputData[columncount+3]
                runperiodstartend = _inputData[columncount+4]
                
                runtime.append(columncount)
                
                # Check that the runperiod is annual this is necessary to create the cost graph
                
                if (runperiodstart[0] != 1) or (runperiodstart[1] != 1) or (runperiodstart[2] != 1):
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                if (runperiodstartend[0] != 12) or (runperiodstartend[1] != 31) or (runperiodstartend[2] != 24):
                    
                    warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
                    print warn
                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                    return -1
                    
                runtimeandname.append((columncount,column))
                    
    def checkruntime(runtime):
        # This function checks that the runtimes for all the inputs are the same by using the runtime list
        # However it doesn't check that the runperiod is annual
        #print runtime

        differenceruntimes = []
        
        # Append the difference in runtimes between all the EnergyPlus outputs to a list

        for count,outputruntime in enumerate(runtime):
            
            try:
                differenceruntimes.append(runtime[count+1]-outputruntime)
            except IndexError:
                pass
                
        # Check that all the runtimes are the same
        
        if all(x == differenceruntimes[0] for x in differenceruntimes) != True:
            
            warn = "In order to graph honeybee generation system results the run period must be set to annual for all the inputs!"
            print warn
            ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
            # If runtimes are not the same return -1
            return -1
            
    # Check discount factor inputs
    
    if (discount_factor > 100) or (discount_factor < 0):
        
        warn = "discount_factor must be entered as a percentage - between 0 and 100!"
        print warn
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
        # If runtimes are not the same return -1
        return -1
            
    if checkruntime(runtime) == -1:
        return -1
    
    else:

        # Return the difference in columns between each set of data e.g daily data is 372
        return (runtimeandname[1][0]-runtimeandname[0][0])
        
def extractfinancialdata(_inputData):
    
    """ This function extracts the finacial data of facilitys' energy generation systems from the _inputData"""
    
    financialdataindexs = []
    
    for columncount, column in enumerate(_inputData):
        
        if isinstance(column, basestring) == True:
            
            if "Generator system financial data" in column:
                
                financialdataindexs.append(columncount)
                
            if ';;;' in column: # Marker for end of Generator system fiancial data
                
                financialdataindexs.append(columncount)

    financialdata = _inputData[financialdataindexs[0]:(int(financialdataindexs[1]))]
    
    # Remove the financial data from _inputData so that energy generation data can be read
    
    new_inputData = []
    
    for index in range(len(_inputData)):
        
        if ((index < financialdataindexs[0]) or (index > (financialdataindexs[1]))):
    
            new_inputData.append(_inputData[index])
            
    return financialdata,new_inputData
    
def checktimestep(Netpurchasedelect,Facilitytotalelectdemand,generatorsproducedelec):
    
    if (len(stringtoFloat(Netpurchasedelect)) != 8760) and  (len(stringtoFloat(Facilitytotalelectdemand)) != 8760) and (len(stringtoFloat(generatorsproducedelec)) != 8760):
        
        warn = "To calculate the financial value of Honeybee generation systems the timestep of the EnergyPlus simulation must be set to hourly.\n" + \
                "To set the timestep to hourly you can do one of the following\n" + \
                "1. Don't set the HBgeneration_ option to True on the Honeybee_Generate EP Output component.\n" + \
                "2. Disconnect the EP Output component from the Honeybee_Run Energy Simulation component\n" + \
                "3. Alternatively set the timestep_ input on the Honeybee_Generate EP Output component to hourly"
        print warn
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
        return -1
    
def checktheinputs(gridelect_cost_schedule,feedin_tariff_schedule):
    
    if (feedin_tariff_schedule == []) or (feedin_tariff_schedule[0] == None):
        
        warn = 'The price of the feed in tariff per Kwh must be specified! \n' + \
        'If a flat cost is used just specify one value, this will be used for all hours of the year otherwise specify 24 hours of data for each month of the year \n' + \
        'that is 288 hours of data for the whole year'
    
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, warn)
        return -1
        
    if (gridelect_cost_schedule == []) or (gridelect_cost_schedule[0] == None):
        

        warn = 'The cost of grid electricty per Kwh must be specified! \n' + \
        'If a flat cost is used just specify one value, this will be used for all hours of the year otherwise specify 24 hours of data for each month of the year \n' + \
        'that is 288 hours of data for the whole year'

        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, warn)
        return -1
        
        
    if (len(gridelect_cost_schedule) > 1) and (len(gridelect_cost_schedule) != 288):

        warn = 'The cost of grid electricty per Kwh must be specified! The cost of grid electricty for each hour of the day for one day in every month of the year was not found! \n' + \
        'if you want to use a flat rate just specify one value this will be used as the grid electricity cost across the year \n' + \
        'Otherwise you must specify the cost of grid electricity for  288 hours of the year, that is for each hour of the day for one day in every month of the year'
        print warn
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, warn)
        return -1
    
    if (len(feedin_tariff_schedule) > 1) and (len(feedin_tariff_schedule) != 288):

        warn = 'The price of the feed in tariff per Kwh must be specified! The cost of grid electricty for each hour of the day for one day in every month of the year was not found! \n' + \
        'if you want to use a flat rate just specify one value this will be used as the grid electricity cost across the year \n' + \
        'Otherwise you must specify the cost of grid electricity for  288 hours of the year, that is for each hour of the day for one day in every month of the year'
        print warn
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, warn)
        return -1

# 1. Check if data is being connected from ReadEP_generation_system_results. If so graph these results, if not generate warning
if ('Whole Building:Facility Net Purchased Electric Energy' in _inputData) and ('Whole Building:Facility Total Electric Demand Power' in _inputData) and any('Electric energy produced by the generator system named - ' in data for data in _inputData) and ('Generator system financial data' in _inputData):
    
    # 2. First extract and then remove financial data from _inputData
    
    allfinancialdata,new_inputData = extractfinancialdata(_inputData)
    
    # 3. Check that all the data is annual data (The EnergyPlus runtime is over the entire year) and that all the runtimes are consistent (the same)
    if checkforhoneybeegeneration(new_inputData) != -1:
        
        # Check the grid elect and tariff inputs
        if checktheinputs(gridelect_cost_schedule,feedin_tariff_schedule) != -1:
        
            # 4. Build lists of data to create the graph
            
            # The net purchased electricity by the Facility in the EnergyPlus simulation in Joules
            Netpurchasedelect = []
            
            # The total electricity demand by the Facility in Watts
            Facilitytotalelectdemand = []
            
            # A list of lists with each list being the electricity produced by a Honeybee generation system 
            # within the facility.
            generatorsproducedelec = []
            
            # Now use the length of each dataset which was found in the function checkforhoneybeegeneration (If no errors were found at step 3. )
            # to extract each dataset from the component input - _inputData and add it to the lists above.
    
            for datanum,data in enumerate(new_inputData):
    
                if isinstance(data, basestring) == True:
                    
                    if data == 'Whole Building:Facility Net Purchased Electric Energy':
    
                        Netpurchasedelect.extend(new_inputData[datanum:(checkforhoneybeegeneration(new_inputData)+datanum)])
                        
                    if data == 'Whole Building:Facility Total Electric Demand Power':
                        
                        Facilitytotalelectdemand.extend(new_inputData[datanum:(checkforhoneybeegeneration(new_inputData)+datanum)])
                       
                    if data.find('Electric energy produced by the generator system named') != -1:
                        
                        generatorsproducedelec.append(new_inputData[datanum:(checkforhoneybeegeneration(new_inputData)+datanum)])
            
            # Once data for Netpurchasedelect,Facilitytotalelectdemand and generatorsproducedelec is extracted,
            # Make sure that in each case the EnergyPlus timestep is hourly otherwise there is not enough data to draw the graph.
            
            if checktimestep(Netpurchasedelect,Facilitytotalelectdemand,generatorsproducedelec) != -1:
                
                
                # 5. Create the lists of data that will draw the cashflow graph
    
                # Create the numbers to slice fiancial data so that each generator systems costs 
                # can be seperated from the whole
                generatorfinancialdatalength = []
                
                for dataCount,data in enumerate(allfinancialdata):
                    if 'generation system name' in data:
                        generatorfinancialdatalength.append(data.replace('generation system name -',''))
                        generatorfinancialdatalength.append(dataCount)
                        
                # Create a different list for each generator system with the name of the generator system 
                # and the total cost of the system - The sum of the cost of all the items in the system.
                
                financialdatabysystem = []
                
                for countstart,Generatorname,countstop in itertools.izip_longest(generatorfinancialdatalength[1::2],generatorfinancialdatalength[::2],generatorfinancialdatalength[3::2]):
                    
                    financialdatabysystem.append(allfinancialdata[countstart:countstop])
                
                # A - Create a list of recurring replacement costs 
                
                replacementitems = []
                
                # B Create a list of annual maintenance costs
                
                maintenancecost = []
                
                # Find all items that require replacement after a number of years; list them along with the Honeybee generation system they are part
                # of (name), the item name, their cost and replacement time in that order.
                
                # Find all annual system maintenance costs list it along with the Honeybee generator system name
          
                for financialdata in financialdatabysystem:
                    for data in financialdata:
                        
                        if data.find(" replacement time = ") != -1:
                            
                            
                            replacementitems.append(list((financialdata[0],data.split('replacement time = ')[0].split(" - ")[0],float(data.split('replacement time = ')[0].split(" - ")[1]),float(data.split('replacement time = ')[1].replace(" years","")))))
                            
                        if data.find("Honeybee system annual maintenance cost") != -1:
                            
                            # The generator system will be the same as replacement items so
                            # order of lists the same no need to put generation system name in this list
                            maintenancecost.append(float(data.split('-')[1]))
                 
                 
                            # Check what each item is
                            #print financialdata[0] # The name of the generation system
                            #print data.split('replacement time = ')[0].split(" - ")[0] # 
                            #print float(data.split('replacement time = ')[0].split(" - ")[1]) #
                            #print float(data.split('replacement time = ')[1].replace(" years",""))
    
                capitalcosts = []
                # C - Create a list of inital capital costs for year zero 
                # Find all the items that will be a capital cost, list them along with the Honeybee generation system they are part
                # of (name), the item name, and item cost
                
                for financialdata in financialdatabysystem:
                    capitalcost = []
                    capitalcost.append(financialdata[0]) # The system name
                    for data in financialdata:
                        
                        if data.find(" replacement time = ") != -1:
                            
                            capitalcost.append(data.split('replacement time = ')[0].split(' - ')[0]) # Item name
                            capitalcost.append(data.split('replacement time = ')[0].split(' - ')[1]) # Item cost
                        
                        # Need to filter out the first item in in financial data - the system name
                        elif data.find(" Honeybee generation system name") == -1: 
                        
                            capitalcost.append(data.split(' - ')[0]) # Item name
                            capitalcost.append(data.split(' - ')[1]) # Item cost
                            
                    capitalcosts.append(capitalcost)
                
                
                # 6. Set up data to draw cashflow graph 
                
                # Create a start point for the graph
                startPt = rc.Geometry.Point3d(0, 0, 0)
                
                #Set defaults for xScale and yScale.
                if _xScale_ != None: xS = _xScale_
                else: xS = 1
                if _yScale_ != None: yS = _yScale_
                else: yS = 1
                
                #Make a chart boundary.
                chartAxes = []
                width = xS*135
                height = yS*50 # - No bar will exceeed 0.80 % of this height or 40
                chartAxes.append(rc.Geometry.Rectangle3d(rc.Geometry.Plane.WorldXY, width, height).ToNurbsCurve())
                
                # Make graph start point
               
                graphstartPt = rc.Geometry.Point3d(0, 0,0)
                
                # Make lists to add graph data to
                dataMeshes = []
                graphText = []; graphTextpoints = []
                TitleText = []; Titletextpoints = []
                textSrfs = []
                axisMeshes = []
                 
                # Make a z axis scale: to scale the data so that the maximum value in the bar graph never exceeds 80% of the height of the chart boundaries
                
                # To make a z axis scale must find the maximum cost that occurs to scale all data by this cost
                
                # Start with finding the capital cost
                capitalcosts_sum = 0
                
                for systemcapcost in capitalcosts:
                    
                    capitalcosts_sum = capitalcosts_sum+sum(stringtoFloat(systemcapcost[2::2]))
                    
                # Find max replacement cost
                
                replacementcosts = []
                
                for replacementitem in replacementitems:
                    
                    replacementcosts.append(replacementitem[2])
                    
                maxreplace_cost = max(replacementcosts)
                
                # Max operation cost XXX
                
                # Find maximum cost for negative axis (The system is costing money,
                # buying equipment, repacing equipment etc), this will be used when drawing axis
                
                maxcostnegitive = capitalcosts_sum
                
                # Use the above to calculate z axis scale
                
                zscale = (height*0.8)/capitalcosts_sum
     
                # 6. Draw capital costs for all the equipment across different generation systems at year zero
                
                def draw2Dgraphbars(startPt,Xposition,Zposition,zscale,color):
                        
                    dataMeshes = []
                    
                    # 1. Create the points of the mesh of the bars themselves
                    
                    facePt1 = rc.Geometry.Point3d(startPt.X , startPt.Z, startPt.Y ) 
                    facePt2 = rc.Geometry.Point3d(startPt.X + Xposition*zscale, startPt.Z, startPt.Y)
                    facePt3 = rc.Geometry.Point3d(startPt.X + Xposition*zscale, startPt.Z + Zposition*zscale, startPt.Y) 
                    facePt4 = rc.Geometry.Point3d(startPt.X, startPt.Z+ Zposition*zscale, startPt.Y )
                    
                    # Create the mesh of the bars themselves
                    
                    barMesh = rc.Geometry.Mesh()
                    for point in [facePt1, facePt2, facePt3, facePt4]:
                        barMesh.Vertices.Add(point)
                    barMesh.Faces.AddFace(0, 1, 2, 3)
                    
                    # Color the mesh faces of the bars themselves
                    barMesh.VertexColors.CreateMonotoneMesh(color)
                    
                    dataMeshes.append(barMesh)
                   
                    return dataMeshes
                            
                # Make datatree of the value of each system - 
                #Positive means worth it, negative means cheaper to buy grid electricity
                
                gensystem_value = DataTree[Object]()
                
                # cost_energy = DataTree[Object]() # XXX future for levelisedcost of energy
                
                gensystem_value_sysnames = []
                
                # Draw the mesh of the cost for each Honeybee generator system, 
                global colors
                colors = [System.Drawing.Color.MediumBlue,System.Drawing.Color.Red,System.Drawing.Color.Yellow,System.Drawing.Color.GhostWhite,System.Drawing.Color.Indigo,System.Drawing.Color.Gold,System.Drawing.Color.Crimson,System.Drawing.Color.Silver]
                
                Zposition = 0
                
                systemCountcolor = 0

                for systemCount,systemcapcost in enumerate(capitalcosts):

                    gensystem_value_sysnames.append(systemcapcost[0])
                    if systemCountcolor == len(colors):
                        # Re-set system count
                        systemCountcolor == 0
                        
                        systemcost = -sum(stringtoFloat(systemcapcost[2::2]))
                        
                        gensystem_value.Add(systemcost, GH_Path(systemCount))
                        
                        # draw2Dgraphbars(startPt,Xposition,Zposition,zscale,color)
                        dataMeshes.extend(draw2Dgraphbars(rc.Geometry.Point3d(graphstartPt.X,graphstartPt.Z + Zposition,graphstartPt.Y),width*0.0375,systemcost,zscale,colors[systemCountcolor]))
                        
                        graphText.append(str(round(systemcost,2)))
                        graphTextpoints.append(rc.Geometry.Point3d(0,(systemcost*zscale)/2, 0))
                        
                        Zposition = Zposition+-(sum(stringtoFloat(systemcapcost[2::2]))*zscale)
                        
                        systemCount = systemCount +1
                        
                    else:
                        
                        systemcost = -sum(stringtoFloat(systemcapcost[2::2]))
                        
                        gensystem_value.Add(systemcost, GH_Path(systemCount))
                        
                        dataMeshes.extend(draw2Dgraphbars(rc.Geometry.Point3d(graphstartPt.X,graphstartPt.Z + Zposition,graphstartPt.Y),width*0.0375,systemcost,zscale,colors[systemCountcolor]))
                        
                        graphText.append(str(round(systemcost,2)))
                        graphTextpoints.append(rc.Geometry.Point3d(0,(systemcost*zscale)/2, 0))
                        
                        Zposition = Zposition+-(sum(stringtoFloat(systemcapcost[2::2]))*zscale)
                        
                        systemCountcolor = systemCountcolor+1
                        
                    
                    # Draw the name of each Honeybee generator system
                    #graphLabels.append(write_3Dtxttag(10,0,10,financialdata[0].replace("' generation system name -",'').replace("'",''),5))
                    
                    # Draw the cost of each Honeybee generator system
        
                    #graphLabels.append(write_3Dtxttag(10,0,10,-sum(stringtoFloat(financialdata[1:])),5))
                    
    
                
                # 7. Graph the cashflow for all the generator systems over 25 years
                
                # First convert grid electcity rates and tariff feed in rates to run period used in simulation,
                # e.g annual,monthly or daily
                
                
                def tariff(tariff_schedule,simulationinterval):
                    ## XXX for now will only use simulations with hourly
                    # timesteps maybe allow other timesteps in the future 
                    
                    
                    if simulationinterval == 1:
                        
                        return sum(tariff_schedule)/288
                        
                    if simulationinterval == 12:
                        
                        return list((sum(tariff_schedule[0:24])/24),(sum(tariff_schedule[24:48]))/24,(sum(tariff_schedule[48:72]))/24,(sum(tariff_schedule[72:96]))/24,(sum(tariff_schedule[96:120]))/24,(sum(tariff_schedule[120:144])/24,(sum(tariff_schedule[144:168]))/24,(sum(tariff_schedule[168:192]))/24,(sum(tariff_schedule[192:216]))/24,(sum(tariff_schedule[216:240]))/24,(sum(tariff_schedule[240:264]))/24,(sum(tariff_schedule[264:288]))/24))
                            
                    if simulationinterval == 365:
                        
                        return ((sum(tariff_schedule[0:24])/24)*31+((sum(tariff_schedule[24:48]))/24)*28+((sum(tariff_schedule[48:72]))/24)*31+((sum(tariff_schedule[72:96]))/24)*30+((sum(tariff_schedule[96:120]))/24)*31+(sum(tariff_schedule[120:144])/24)*30+((sum(tariff_schedule[144:168]))/24)*31+((sum(tariff_schedule[168:192]))/24)*31+((sum(tariff_schedule[192:216]))/24)*30+((sum(tariff_schedule[216:240]))/24)*31+((sum(tariff_schedule[240:264]))/24)*30+((sum(tariff_schedule[264:288]))/24)*31)
                    
                    
                    # Check the data of tariff schedule
                    if len(tariff_schedule) == 0:
                        
                        warn = "To draw the honeybee generation system cashflow graph the tariff_schedule must be specifed !"
                        print warn
                        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                        
                        return -1 
                    
                    if simulationinterval == 8760:
                    
                        if len(tariff_schedule) == 288:
                            
                            return (tariff_schedule[0:24]*31)+(tariff_schedule[24:48]*28)+(tariff_schedule[48:72]*31)+(tariff_schedule[72:96]*30)+(tariff_schedule[96:120]*31)+(tariff_schedule[120:144]*30)+(tariff_schedule[144:168]*31)+(tariff_schedule[168:192]*31)+(tariff_schedule[192:216]*30)+(tariff_schedule[216:240]*31)+(tariff_schedule[240:264]*30)+(tariff_schedule[264:288]*31)
                        
                        if len(tariff_schedule) == 1:
                            # If flatrate - set it to every hour of the year 
                            return tariff_schedule*8760
                            
                def gridelectricty(gridelectcost_schedule,simulationinterval):
                    ## XXX for now will only use simulations with hourly
                    # timesteps maybe allow other timesteps in the future 
                    
                    if simulationinterval == 1:
                        
                        return sum(gridelectcost_schedule)/288
                        
                    if simulationinterval == 12:
                        
                        return (sum(gridelectcost_schedule[0:24])/24),(sum(gridelectcost_schedule[24:48]))/24,(sum(gridelectcost_schedule[48:72]))/24,(sum(gridelectcost_schedule[72:96]))/24,(sum(gridelectcost_schedule[96:120]))/24,(sum(gridelectcost_schedule[120:144])/24,(sum(gridelectcost_schedule[144:168]))/24,(sum(gridelectcost_schedule[168:192]))/24,(sum(gridelectcost_schedule[192:216]))/24,(sum(gridelectcost_schedule[216:240]))/24,(sum(gridelectcost_schedule[240:264]))/24,(sum(gridelectcost_schedule[264:288]))/24)
                            
                    if simulationinterval == 365:
                    
                        return list((sum(gridelectcost_schedule[0:24])/24)*31+((sum(gridelectcost_schedule[24:48]))/24)*28+((sum(gridelectcost_schedule[48:72]))/24)*31+((sum(gridelectcost_schedule[72:96]))/24)*30+((sum(gridelectcost_schedule[96:120]))/24)*31+(sum(gridelectcost_schedule[120:144])/24)*30+((sum(gridelectcost_schedule[144:168]))/24)*31+((sum(gridelectcost_schedule[168:192]))/24)*31+((sum(gridelectcost_schedule[192:216]))/24)*30+((sum(gridelectcost_schedule[216:240]))/24)*31+((sum(gridelectcost_schedule[240:264]))/24)*30+((sum(gridelectcost_schedule[264:288]))/24)*31)
                    
                    if len(gridelectcost_schedule) == 0:
                        
                        warn = "To draw the honeybee generation system cashflow graph the gridelectcost_schedule must be specifed !"
                        print warn
                        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warn)
                        
                        return -1 
    
                    if simulationinterval == 8760:
                        
                        if len(gridelectcost_schedule) == 1:
                            
                            # If flatrate - set it to every hour of the year 
                            return gridelectcost_schedule*8760
                            
                        if len(gridelectcost_schedule) == 288:
                            
                            return (gridelectcost_schedule[0:24]*31)+(gridelectcost_schedule[24:48]*28)+(gridelectcost_schedule[48:72]*31)+(gridelectcost_schedule[72:96]*30)+(gridelectcost_schedule[96:120]*31)+(gridelectcost_schedule[120:144]*30)+(gridelectcost_schedule[144:168]*31)+(gridelectcost_schedule[168:192]*31)+(gridelectcost_schedule[192:216]*30)+(gridelectcost_schedule[216:240]*31)+(gridelectcost_schedule[240:264]*30)+(gridelectcost_schedule[264:288]*31)
                
                class HBsystemgenerator(object):
                    """Contains cashflow information about each Honeybee generation system being graphed"""
                    def __init__(self,generatorname,generatorproducedelec):
                        
                        self.name = generatorname
                        self.annualgenincome = []
                        # A list of the electricity that the generator produced
                        # throughout the whole year
                        self.genproduced_elect = generatorproducedelec
        
                    def cashflow_sim_interval(self,income):
                        
                        self.annualgenincome.append(income)
                        
                    def totalincome(self):
                        
                        return sum(self.annualgenincome)
                
                class simulation_timestep(object):
                    """Calculates the cashflow for each simulation timestep"""
                    def __init__(self,interval,tariffratehour,gridelectratehour,electdemandhour,simulationtimestep,generators):
                        
                        # Convert electdemandhour into energy as EnergyPlus only outputs it as 
                        # power (Not sure why?!!)
                        # Runperiod is annual
                            
                        self.genproducedelect = []
                        
                        for generator in generators:
                            
                            # Append the generator produced energy at this simulation timestep
                            self.genproducedelect.append(generator.genproduced_elect[simulationtimestep])
                        
                        # Get the total electricity produced by all generators at this simulation timestep
                        self.totalproducedelect = sum(self.genproducedelect)
                        
                        # electtogrid negative if no elect fed to grid for this simulation timestep
                        electtogrid = self.totalproducedelect - electdemandhour
                        
                        if electtogrid > 0:
                            # In this simulation timestep electricity is fed to the grid
                            
                            # Calculate the monetary savings of having electricity produced onsite for each generator
                            # for this simulation timestep

                            incometariff = (electtogrid)*tariffratehour
                            
                            electcostssaved = (electdemandhour)*gridelectratehour
                        
                            for generator in generators:
                                
                                # What percentage of electricity did this generator produce in this timestep?
                                genelect_percent = generator.genproduced_elect[simulationtimestep]/self.totalproducedelect
    
                                # Add the monetary savings for this timestep for each generator to the generator
                                generator.cashflow_sim_interval((incometariff+electcostssaved)*genelect_percent)
                        
                        else:
                            # In this simulation timestep no surplus electricity is produced and all
                            # electricity is consumed by the facility
                            for generator in generators:
                                # Calculate the monetary savings of having electricity produced onsite for each generator
                                # and add it to that generator.
        
                                generator.cashflow_sim_interval(((generator.genproduced_elect[simulationtimestep]))*gridelectratehour)
                                
                # Determine simulation interval
                
                if len(stringtoFloat(Facilitytotalelectdemand)) == 1:
                    # Runperiod set to annual
                    simulationinterval = 1
               
                if len(stringtoFloat(Facilitytotalelectdemand)) == 12:
                    # Runperiod set to monthly
                    simulationinterval = 12
                    
                if len(stringtoFloat(Facilitytotalelectdemand)) == 365:
                    # Runperiod set to daily
                    simulationinterval= 365
                    
                if len(stringtoFloat(Facilitytotalelectdemand)) == 8760:
                    # Runperiod set to hourly
                    # For now only hourly timesteps will be used so the simulation inteveral will always be 8760
                    simulationinterval = 8760
                
                # Create a list of Honeybee system generators
                
                facilityHBgenerators = []
                
                for generatorproducedelct in generatorsproducedelec:
                    
                    facilityHBgenerators.append(HBsystemgenerator(generatorproducedelct[0].replace('Electric energy produced by the generator system named -',''),stringtoFloat(generatorproducedelct)))
                
                # Convert tariff and grid electricity schedules into a list so that
                # one index is available for every simulation timestep.
                
                if (tariff(feedin_tariff_schedule,simulationinterval) != -1) and (gridelectricty(gridelect_cost_schedule,simulationinterval) != -1):
    
                    tariffrate_siminterval = tariff(feedin_tariff_schedule,simulationinterval)
                    gridelect_siminterval = gridelectricty(gridelect_cost_schedule,simulationinterval)
                    
                    # Run the simulation_timestep class for each timestep
                    # - this will calculate the monteary savings for each generator at each timestep by the facility either not having to buy 
                    # electricty or by selling electricity back to the grid
                    # append this information to each generators' list called annualgenincome
                    
                    for timestep,electdemand in enumerate((stringtoFloat(Facilitytotalelectdemand))):
                        
                        simulation_timestep(simulationinterval,tariffrate_siminterval[timestep],gridelect_siminterval[timestep],electdemand,timestep,facilityHBgenerators)
                    
                    # Find the annual monteary savings by summing together 
                    # each timestep in each generators' list annualgenincome
                    # then graph it
                    
                    # Contains the name of each Honeybee system generator and then its annual income
                    genmontearyvalue = []
     
                    for generator in facilityHBgenerators:
                        
                        genmontearyvalue.append(generator.name) 
                        genmontearyvalue.append(generator.totalincome())
                        
                    # If a discount factor is used, calculate the discount factor
                    
                    # Graph these monteary savings for years 1 to 25
                    for year in range(1,26):
    
                        Zposition1 = 0
                        
                        # If a discount factor is used, calculate the discount factor for the year
                        
                        if discount_factor is not None:
                            
                            fdiscount = 1/((1+(discount_factor/100))**year)
                        else:
                            fdiscount = 1
                            
                        # Cant use enumerate for systemcountcolors as need to reset count everytime
                        # It exceeds the length of color list - use the same colors over again
                        # thus create custom count
                        systemcountcolors = 0 
                        
                        for systemCount,(saving,name) in enumerate(zip(genmontearyvalue[1::2],genmontearyvalue[::2])):
                            
                            if systemcountcolors == len(colors):
                                # Re-set systemcolorcount
                                systemcountcolors == 0
                                
                                # Add saving to respective Honeybee generator 
                                gensystem_value.Add(saving*fdiscount, GH_Path(systemCount))
                                
                                dataMeshes.extend(draw2Dgraphbars(rc.Geometry.Point3d(year*width/25,0, Zposition1),width*0.03,saving*fdiscount,zscale,colors[systemcountcolors]))
                                
                                ##graphText.append(str(saving))
                                ##graphTextpoints.append(rc.Geometry.Point3d(0,(width*0.0375)/2, (systemcost*zscale)/2))
                                
                                Zposition1 = Zposition1+(saving*zscale*fdiscount)
                                
                                
                                # Draw number on mesh
                                #(xposition,yposition,zposition,text,size)
                                #graphLabels.extend(write_3Dtxttag(year*10,0,float(saving),float(saving),5))
             
                                # Draw generator system name on mesh 
                                #graphLabels.extend(write_3Dtxttag(year*10,0,float(saving),name,5))
                                
                                
                            else:
                                
                                # Add saving to respective Honeybee generator 
                                gensystem_value.Add(saving*fdiscount, GH_Path(systemCount))
                                
                                dataMeshes.extend(draw2Dgraphbars(rc.Geometry.Point3d(year*width/25,0, Zposition1),width*0.03,saving*fdiscount,zscale,colors[systemcountcolors]))
                                
                                Zposition1 = Zposition1+(saving*zscale*fdiscount)
                                
                                ##graphText.append(str(systemcost))
                                ##graphTextpoints.append(rc.Geometry.Point3d(0,(width*0.03)/2, (systemcost*zscale)/2))
                        
                                
                                # Draw number on mesh
                                #(xposition,yposition,zposition,text,size)
                                #graphLabels.extend(write_3Dtxttag(year*10,0,float(saving),float(saving),5))
             
                                # Draw generator system name on mesh 
                                #graphLabels.extend(write_3Dtxttag(year*10,0,float(saving),name,5))
                                
                                # Graph costs for replacing items e.g batteries after 5 years
                            
                            Zpositionreplace = 0
                            for replacementitem in replacementitems:
                                
                                # If year is divisible by replacement time include replacement cost 
        
                                if year % float(replacementitem[3]) == 0:
                                    
                                    dataMeshes.extend(draw2Dgraphbars(rc.Geometry.Point3d(year*width/25,0, Zpositionreplace),width*0.03,-replacementitem[2]*fdiscount,zscale,colors[systemcountcolors]))
                                    
                                    Zpositionreplace = Zpositionreplace - replacementitem[2]*zscale*fdiscount
                                    
                                    # Add replacement cost to respective Honeybee generator 
                                    gensystem_value.Add(-replacementitem[2]*fdiscount, GH_Path(systemCount))
                                        
                                    ##graphText.append(str(systemcost))
                                    ##graphTextpoints.append(rc.Geometry.Point3d(0,(width*0.03)/2, (systemcost*zscale)/2))
                        
                                        
                                    # Draw number on mesh
                                    #graphLabels.extend(write_3Dtxttag(year*10,0,float(replacementitem[2]),float(replacementitem[2]),5))
                 
                                    # Draw generator system name on mesh 
                                    #graphLabels.extend(write_3Dtxttag(year*10,0,float(replacementitem[2]),name,5))
                            
                            # Add annual maintenance costs and draw them
                            
                            gensystem_value.Add(-maintenancecost[systemCount])
                            
                            systemcountcolors = systemcountcolors+1
                    
                    
                # Draw graph axis
                    
                            
                def verticaldrawAxis(startPt,Max,Min,zscale):
                    
                    dataMeshes = []
                    textSrfs = []
                    
                    # 1. Draw markings along the vertical axis
                    
                    # Make it so the axis always ends 15% of the min above the highest graph point
                    # and 15% below the lowest graph point 
                    posDomain = Max+(Max*0.15)
                    negDomain = Min+(Min*0.15)
                    
                    for marking in range(0,int(posDomain),5000):
                        
                        facePt1 = rc.Geometry.Point3d(startPt.X - 1, startPt.Y + (marking*zscale) - 0.2, startPt.Z)
                        facePt2 = rc.Geometry.Point3d(startPt.X, startPt.Y + (marking*zscale) - 0.2 , startPt.Z )
                        facePt3 = rc.Geometry.Point3d(startPt.X - 1, startPt.Y + (marking*zscale), startPt.Z )   
                        facePt4 = rc.Geometry.Point3d(startPt.X, startPt.Y +(marking*zscale) , startPt.Z) 
                        
                        # Create the text and text point
                        
                        textSrf = lb_visualization.text2srf([str(marking)], [rc.Geometry.Point3d(startPt.X-4,startPt.Y + (marking*zscale)-0.35,startPt.Z)],'Verdana' , 0.5, False)
                        textSrfs.extend(textSrf[0])
                        
                        # Create the mesh of the marking themselves
                        
                        barMesh = rc.Geometry.Mesh()
                        
                        for point in [facePt1, facePt2, facePt3, facePt4]:
                            barMesh.Vertices.Add(point)
                        barMesh.Faces.AddFace(0, 1, 3, 2)
                        
                        # Color the mesh faces of the markings themselves
                        barMesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.Black)
                        
                        dataMeshes.append(barMesh)
                        
                    for marking in range(0,int(negDomain),5000):
    
                        facePt1 = rc.Geometry.Point3d(startPt.X - 1, startPt.Y + (-marking*zscale) - 0.2, startPt.Z)
                        facePt2 = rc.Geometry.Point3d(startPt.X, startPt.Y + (-marking*zscale) - 0.2 , startPt.Z )
                        facePt3 = rc.Geometry.Point3d(startPt.X - 1, startPt.Y + (-marking*zscale), startPt.Z )   
                        facePt4 = rc.Geometry.Point3d(startPt.X, startPt.Y +(-marking*zscale) , startPt.Z) 
                        
                        # Create the text and text point
                        
                        textSrf = lb_visualization.text2srf([str(-marking)], [rc.Geometry.Point3d(startPt.X-4,startPt.Y + (-marking*zscale)-0.35,startPt.Z)],'Verdana' , 0.5, False)
                        textSrfs.extend(textSrf[0])
                        
                        # Create the mesh of the marking themselves
                        
                        barMesh = rc.Geometry.Mesh()
                        for point in [facePt1, facePt2, facePt3, facePt4]:
                            barMesh.Vertices.Add(point)
                        barMesh.Faces.AddFace(0, 1, 3, 2)
                        
                        # Color the mesh faces of the markings themselves
                        barMesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.Black)
                        
                        dataMeshes.append(barMesh)
                        
                    # 2. Create the vertical axis
            
                    facePt1 = rc.Geometry.Point3d(startPt.X + 0.15, startPt.Y + -negDomain*zscale, startPt.Z)
                    facePt2 = rc.Geometry.Point3d(startPt.X, startPt.Y + -negDomain*zscale, startPt.Z )
                    facePt3 = rc.Geometry.Point3d(startPt.X + 0.15, startPt.Y + posDomain*zscale, startPt.Z )   
                    facePt4 = rc.Geometry.Point3d(startPt.X, startPt.Y + posDomain*zscale, startPt.Z) 
                    
                    # Create the mesh of the bars themselves
                    
                    barMesh = rc.Geometry.Mesh()
                    for point in [facePt1, facePt2, facePt3, facePt4]:
                        barMesh.Vertices.Add(point)
                    barMesh.Faces.AddFace(0, 1, 3, 2)
                    
                    # Color the mesh faces of the bars themselves
                    barMesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.Black)
                    
                    dataMeshes.append(barMesh)
                    
                    return dataMeshes,textSrfs
                    
                    
                def horizontialdrawAxis(startPt,verticalMin,verticalMax,zscale,width):
                    
                    # 3. Draw markings along the horizontial axis
    
                    dataMeshes = []
                    
                    # The vertical axis in verticaldrawAxis is set up so that
                    # that it is always 15% below the lowest graph point need to take this into account here
                    
                    markingdist = width/26
    
                    verticalMin = verticalMin+verticalMin*0.15
                    graphZaxis = verticalMin + verticalMax*0.15
    
                    for year,marking in enumerate(range(0,width,int(width/26))):
                        
                        facePt1 = rc.Geometry.Point3d(startPt.X + marking + 0.1, startPt.Y - (verticalMin*zscale) , startPt.Z)
                        facePt2 = rc.Geometry.Point3d(startPt.X + marking , startPt.Y - (verticalMin*zscale), startPt.Z )
                        facePt3 = rc.Geometry.Point3d(startPt.X + marking + 0.1, (startPt.Y - (verticalMin*zscale))+ graphZaxis*zscale , startPt.Z )   
                        facePt4 = rc.Geometry.Point3d(startPt.X + marking , (startPt.Y -(verticalMin*zscale))+ graphZaxis*zscale, startPt.Z) 
                        
                        
                        # Create the text and text point
                       
                        textSrf = lb_visualization.text2srf([str(year)], [rc.Geometry.Point3d(startPt.X+ marking+markingdist/2,startPt.Y - (verticalMin*zscale),startPt.Z)],'Verdana' , 0.5, False)
                        textSrfs.extend(textSrf[0])
                        
                        # Create the mesh of the marking themselves
                        
                        barMesh = rc.Geometry.Mesh()
                        
                        for point in [facePt1, facePt2, facePt3, facePt4]:
                            barMesh.Vertices.Add(point)
                        barMesh.Faces.AddFace(0, 1, 3, 2)
                        
                        # Color the mesh faces of the markings themselves
                        barMesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.Black)
                        
                        dataMeshes.append(barMesh)
                        
                    # 4.  Create the horizontial axis
                    
                    facePt1 = rc.Geometry.Point3d(startPt.X + width*zscale, startPt.Y + 0.15, startPt.Z)
                    facePt2 = rc.Geometry.Point3d(startPt.X, startPt.Y , startPt.Z )
                    facePt3 = rc.Geometry.Point3d(startPt.X + width*zscale, startPt.Y, startPt.Z )   
                    facePt4 = rc.Geometry.Point3d(startPt.X, startPt.Y+ 0.15, startPt.Z) 
                    
                    # Create the mesh of the bars themselves
                    
                    barMesh = rc.Geometry.Mesh()
                    for point in [facePt1, facePt2, facePt3, facePt4]:
                        barMesh.Vertices.Add(point)
                    barMesh.Faces.AddFace(0, 1, 3, 2)
                    
                    # Color the mesh faces of the bars themselves
                    barMesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.Black)
                    
                    dataMeshes.append(barMesh)
    
                    return dataMeshes,textSrfs
                        
                
                axisstartPt = rc.Geometry.Point3d(-2,0 ,0 )
                
                # Find the maximumum cost for positive axis (The system is earning money
                # by saving electricity, feed into grid etc), this will be used when drawing axis
                
                # Find max electricity saving
                
                electsaving = sum(genmontearyvalue[1::2])
                
                maxcostpositive = electsaving
                
                axisMeshes.extend(verticaldrawAxis(axisstartPt,maxcostpositive,maxcostnegitive,zscale)[0]) # Draw graph axis XXX - Need to change genmontearyvalue[1::2][0] to max
                axisMeshes.extend(verticaldrawAxis(axisstartPt,maxcostpositive,maxcostnegitive,zscale)[1])
                
                axisMeshes.extend(horizontialdrawAxis(graphstartPt,maxcostnegitive,maxcostpositive,zscale,width)[0])
                textSrfs.extend(horizontialdrawAxis(graphstartPt,maxcostnegitive,maxcostpositive,zscale,width)[1])
                
                """
                # Draw graph text 
                for count, Text in enumerate(graphText):
    
                    textSrf = lb_visualization.text2srf([Text], [graphTextpoints[count]],'Verdana' , 0.5, False)
                    dataMeshes.extend(textSrf[0])
                """
                    
                branchesNPC = gensystem_value.Branches
                paths = gensystem_value.Paths
                
                #branchesCoE = cost_energy.Branches ## XXX for future levelised cost of electricity
                
                 # Calculate net present cost for each system
                sumBranchesNPC = [[round(sum(item),2)] for item in branchesNPC]
                
                # Calculate the levelised cost of energy for each system XXX
                #sumBranches_costenergy = [[round(sum(item),2)] for item in branchesCoE ]
                
                gensystem_value.ClearData()
                
                for item in range(gensystem_value.BranchCount):
                    
                    gensystem_value.Add(str(gensystem_value_sysnames[item]), paths[item])
                    
                    if currency_ != None:
                        gensystem_value.Add("Generation system Net present cost in "+str(currency_), paths[item])
                    else:
                        
                        gensystem_value.Add("Generation system Net present cost", paths[item])
                        
                    gensystem_value.AddRange(sumBranchesNPC[item], paths[item])
                
                # Print a warning about currency
                if currency_ == None:
                    print "You have not specified the currency of the financial data that you are using, so no currency will be displayed"
                
    
                if _basePoint_ != None and _basePoint_ != rc.Geometry.Point3d.Origin:
                    moveTransform = rc.Geometry.Transform.Translation(_basePoint_.X, _basePoint_.Y, _basePoint_.Z)
                    for geo in dataMeshes: geo.Transform(moveTransform)
                    for geo in axisMeshes: geo.Transform(moveTransform)
                    for geo in textSrfs: geo.Transform(moveTransform)
                        
                    
elif ('Whole Building:Facility Net Purchased Electric Energy' in _inputData) or ('Whole Building:Facility Total Electric Demand Power' in _inputData) or any('Electric energy produced by the generator system named - ' in data for data in _inputData) or ('Generator system financial data' in _inputData) :
    
    warn = 'If you are trying to draw the Honeybee generation system cashflow graph you must connect totalelectdemand,netpurchasedelect, \n'+\
           'generatorproducedenergy and financialdata outputs from the readEP generation system results component, as this component needs all that data to draw the graph'

    w = gh.GH_RuntimeMessageLevel.Warning
    ghenv.Component.AddRuntimeMessage(w, warn)
    
