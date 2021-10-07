"""
Benchmark impact of heterogeneous element size
"""

import cycler
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from mantid.simpleapi import (
    ConvertUnits,
    CreateSampleWorkspace,
    EditInstrumentGeometry,
    SetSample,
    MultipleScatteringCorrection,
    mtd,
)

# ----------------------- #
# make an empty workspace #
# ----------------------- #
# Create a fake workspace with TOF data
ws = CreateSampleWorkspace(Function='Powder Diffraction',
                            NumBanks=2,
                            BankPixelWidth=1,
                            XUnit='TOF',
                            XMin=1000,
                            XMax=10000,)
# Fake instrument
EditInstrumentGeometry(ws,
                        PrimaryFlightPath=5.0,
                        SpectrumIDs=[1, 2],
                        L2=[2.0, 2.0],
                        Polar=[10.0, 90.0],
                        Azimuthal=[0.0, 45.0],
                        DetectorIDs=[1, 2],
                        InstrumentName="Instrument")
# set sample and container
SetSample(
        ws,
        Geometry={
            "Shape": "Cylinder",
            "Center": [0., 0., 0.],
            "Height": 1.0,  # cm
            "Radius": 0.3,  # cm
        },
        Material = {
            "ChemicalFormula": "La-(B11)5.94-(B10)0.06",
            "SampleNumberDensity": 0.1,
        },
        ContainerMaterial = {
            "ChemicalFormula": "V",
            "SampleNumberDensity": 0.0721,
        },
        ContainerGeometry = {
            "Shape": "HollowCylinder",
            "Height": 1.0,  # cm
            "InnerRadius": 0.3,  # cm
            "OuterRadius": 0.35,  # cm
            "Center": [0., 0., 0.],
        }
    )

# to wavelength
ConvertUnits(InputWorkspace=ws,
                OutputWorkspace=ws,
                Target="Wavelength",
                EMode="Elastic")

# Step_1: analyze the impact of element size during numerical integration
# NOTE: 0.5mm is the maximum as the container thickness is 0.5mm (0.35 cm - 0.3cm)
# - 0.1 mm will lead to LLVM memory error, so we have to stop at 0.2 mm
elementsizes = [
    0.5, 0.45, 0.4, 
    0.35, 0.3, 0.25,
    0.2,
    0.15, 0.1,
    ]

clrs = plt.cm.plasma(np.linspace(0.3, 1.0,len(elementsizes)))
mpl.rcParams['axes.prop_cycle'] = cycler.cycler('color', clrs)

fig, ax = plt.subplots(1, 2)

for es in elementsizes:
    print(f"ElementSize = {es}")
    # Run the multiple scattering correction
    rst = MultipleScatteringCorrection(
        InputWorkspace = ws,
        Method="SampleAndContainer",
        ElementSize=elementsizes[0],
        ContainerElementSize=es,
        OutputWorkspace="rst",
    )
    outws = mtd["rst_sampleAndContainer"]
    
    for specID in (0, 1):
        x = outws.readX(specID)
        x = 0.5 * (x[1:] + x[:-1])
        y = outws.readY(specID)
        # plot
        ax[specID].plot(x, y, label=f"{es} mm")

# config the figure
ax[0].set_xlabel("wv/angstrom")
ax[1].set_xlabel("wv/angstrom")
ax[0].set_ylabel("ms_factor")
ax[1].legend()

#
plt.show()