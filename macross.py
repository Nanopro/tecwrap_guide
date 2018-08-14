import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

# Uncomment the following line to connect to a running instance of Tecplot 360:
# tp.session.connect()

tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
    command="SetFluidProperties Incompressible='F' Density=1 SpecificHeat=2.5 UseSpecificHeatVar='F' SpecificHeatVar=1 GasConstant=287 UseGasConstantVar='F' GasConstantVar=1 Gamma=1.41 UseGammaVar='F' GammaVar=1 Viscosity=1 UseViscosityVar='F' ViscosityVar=1 Conductivity=1 UseConductivityVar='F' ConductivityVar=1")
tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
    command="SetFieldVariables ConvectionVarsAreMomentum='F' UVar=5 VVar=6 WVar=7 ID1='Temperature' Variable1=13 ID2='Pressure' Variable2=10")
tp.macro.execute_extended_command(command_processor_id='CFDAnalyzer4',
    command="Integrate [6] VariableOption='MassFlowRate' XOrigin=0 YOrigin=0 ZOrigin=0 ScalarVar=1 Absolute='T' ExcludeBlanked='F' XVariable=1 YVariable=2 ZVariable=3 IntegrateOver='Cells' IntegrateBy='Zones' IRange={MIN =1 MAX = 0 SKIP = 1} JRange={MIN =1 MAX = 0 SKIP = 1} KRange={MIN =1 MAX = 0 SKIP = 1} PlotResults='F' PlotAs='Result' TimeMin=0 TimeMax=0")
# End Macro.

