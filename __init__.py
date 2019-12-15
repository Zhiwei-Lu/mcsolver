from tkinter import Tk
from multiprocessing import Pool, freeze_support
import numpy as np
import guiMain as gui
import Lattice as lat
import mcMain as mc

global bondList,LMatrix,pos,nsweep,nthermal,Lx,Ly,Lz,algorithm

def startMC(param): # start MC for Ising model
    global bondList,LMatrix,pos,nsweep,nthermal,Lx,Ly,Lz,algorithm
    # unzip all global parameters for every processing
    ID, T, bondList,LMatrix,pos,S,nsweep,nthermal,Lx,Ly,Lz,algorithm=param
    mcslave=mc.MC(ID,LMatrix,pos,S,bondList,T,Lx,Ly,Lz)
    mData, eData=np.array(mcslave.mainLoopViaCLib(nsweep=nsweep,nthermal=nthermal,algo=algorithm))
    mData=abs(mData)/Lx/Ly/Lz
    eData/=(Lx*Ly*Lz)
    return ID, T, mData, eData

def startMCForOn(param): # start MC for O(n) model
    #global bondList,LMatrix,pos,nsweep,nthermal,Lx,Ly,Lz,algorithm
    # unzip all global parameters for every processing
    ID, T, bondList,LMatrix,pos,S,nsweep,nthermal,Lx,Ly,Lz,algorithm=param
    mcslave=mc.MC(ID,LMatrix,pos,S,bondList,T,Lx,Ly,Lz)
    mcslave.mainLoopViaCLib_On(nsweep=nsweep,nthermal=nthermal,algo=algorithm)
    #mData=abs(mData)/Lx/Ly/Lz
    #eData/=(Lx*Ly*Lz)

def startSimulaton():
    global bondList,LMatrix,pos,nsweep,nthermal,Lx,Ly,Lz,algorithm
    gui.submitBtn.config(state='disabled')
    # get lattice
    a1=gui.latticeGui[0].report()
    a2=gui.latticeGui[1].report()
    a3=gui.latticeGui[2].report()
    LMatrix=np.array([a1,a2,a3])
    print('Lattice matrix:')
    print(LMatrix)

    # get supercell size
    Lx, Ly, Lz=[int(x) for x in gui.supercellGui.report()]
    print('supercell:')
    print(Lx,Ly,Lz)

    # get oribtal position and spin state
    pos=np.array([ele[3] for ele in gui.OrbListBox.infoData])
    S=[ele[2] for ele in gui.OrbListBox.infoData]
    print('positions:')
    print(pos)
    print('spin state:',S)

    # get bonds
    bondList=[lat.Bond(bond_data[2][0],bond_data[2][1],\
                       np.array(bond_data[2][2]),\
                       bond_data[1][0],bond_data[1][1],bond_data[1][2]) \
                        for bond_data in gui.BondBox.infoData]
        
    print('bonds:')
    print(bondList)

    # get TList
    T0, T1, nT=gui.TListGui.report()
    TList=np.linspace(T0,T1,int(nT))
    print('Temperature:')
    print(TList)

    # get thermalizations and sweeps
    nthermal, nsweep = [int(x) for x in gui.MCparamGui.report()]
    print('thermalizations and sweeps:')
    print(nthermal, nsweep)

    # get model and algorithm
    modelType = gui.modelGui.get()
    print('Model:',modelType)
    algorithm = gui.algorithmGui.get()
    print('Algorithm:',algorithm)

    # get ncores
    ncores= int(gui.coreGui.report()[0])
    print('using %d cores'%ncores)

    # model and algorithm branches
    if(modelType=='Ising'):
        if algorithm!='Metroplis' and algorithm!='Wolff':
            print('For now, only Metroplis and Wolff algorithm is supported for Ising model')
            gui.submitBtn.config(state='normal')
            return
        
        paramPack=[]
        for iT, T in enumerate(TList):
            paramPack.append([iT,T,bondList,LMatrix,pos,S,nsweep,nthermal,Lx,Ly,Lz,algorithm])
        
        TResult=[];magResult=[];susResult=[];energyResult=[];capaResult=[]
        pool=Pool(processes=ncores)
        for result in pool.imap_unordered(startMC,paramPack):
            ID, T, mData, eData =result
            TResult.append(T)
            magResult.append(np.mean(mData))
            susResult.append(np.std(mData))
            energyResult.append(np.mean(eData))
            capaResult.append(np.std(eData))
        pool.close()
        gui.updateResultViewer(TList=TResult, magList=magResult)

        f=open('./result.txt','w')
        f.write('#Temp #Spin    #Susc      #energy  #capacity\n')
        for T, mag, sus, energy, capa in zip(TResult, magResult, susResult, energyResult, capaResult):
            f.write('%.3f %.6f %.6f %.6f %.6f\n'%(T, mag, sus, energy, capa))
        f.close()

        gui.submitBtn.config(state='normal')
        return
    elif(modelType=='XY' or modelType=='Heisenberg'):
        gui.submitBtn.config(state='normal')
        return
        for orb in gui.OrbListBox.infoData:  # add the single ion anisotropy via self-bonding method
            bondList.append(lat.Bond(orb[0],orb[0],np.array([0,0,0]),orb[4][0],orb[4][1],orb[4][2]))
        for bond in bondList:
            bond.On=True # switch on the vector type bonding
        if algorithm!='Metroplis':
            print('For now, only Metroplis algorithm is supported for O(n) model')
            gui.submitBtn.config(state='normal')
            return

        paramPack=[]
        for iT, T in enumerate(TList):
            paramPack.append([iT,T,bondList,LMatrix,pos,S,nsweep,nthermal,Lx,Ly,Lz,algorithm])
        
        startMCForOn(paramPack[0])

        #TResult=[];magResult=[];susResult=[];energyResult=[];capaResult=[]
        #pool=Pool(processes=ncores)
        #for result in pool.imap_unordered(startMC,paramPack):
        #    ID, T, mData, eData =result
        #    TResult.append(T)
        #    magResult.append(np.mean(mData))
        #    susResult.append(np.std(mData))
        #    energyResult.append(np.mean(eData))
        #    capaResult.append(np.std(eData))
        #pool.close()
        #gui.updateResultViewer(TList=TResult, magList=magResult)

        #f=open('./result.txt','w')
        #f.write('#Temp #Spin    #Susc      #energy  #capacity\n')
        #for T, mag, sus, energy, capa in zip(TResult, magResult, susResult, energyResult, capaResult):
        #    f.write('%.3f %.6f %.6f %.6f %.6f\n'%(T, mag, sus, energy, capa))
        #f.close()

        gui.submitBtn.config(state='normal')
        return
        

    print('For now, only Ising model is supported')
    gui.submitBtn.config(state='normal')
    return
            
if __name__ == '__main__': # crucial for multiprocessing in Windows
    freeze_support()
    app=Tk(className='mc solver v1.0')
    gui.loadEverything(app,startSimulaton)
    app.mainloop()