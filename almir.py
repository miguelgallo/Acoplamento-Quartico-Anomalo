from __future__ import division, print_function
import uproot
import uproot4
import numpy as np
import awkward as ak
import pandas as pd
#import numba as nb
import scipy.constants
import uproot_methods.convert
import h5py
from math import *
import sys
import uproot_methods



def open_files( file , array_ ): # Funcao que ler e abre as trees das nTuplas
    root =  uproot4.open(file)
    tree = root['demo/Events']
    lista = []
    for events in tree.iterate( [array_] , step_size="100 MB" , library="ak" ):
        lista.append( np.array( events[ array_ ][:,0] ) ) 
        #print( events[ array_ ][:,0] ) 
        #merda =  np.array( pd.DataFrame( array[ array_ ].tolist() )[0] )
    #print(lista)    
    return np.concatenate( lista )

def open_files_PF( file , array_ ):
    root_ = uproot.open( file )['demo/Events']
    merda = root_[ array_ ].array()
    return merda

def open_files_muon( file , array_ ):
    root_ = uproot.open( file )['demo/Events']
    merda = np.array( pd.DataFrame(root_[ array_ ].array())[0])
    return merda

def almir( file ): # Funcao que retorna um DataFrame que contem a massa invariante do WW, pt do par de le
  
  
    trigger = ( open_files_PF( file , 'HLT_pass') ==  1 )[:,3]
  
    Mw = 80.379 # massa do boson W
    
    jetAK8_pt = open_files_muon( file , 'jetAK8_pt')[trigger]
    jetAK8_prunedMass = open_files_muon( file , 'jetAK8_prunedMass')[trigger]
    jetAK8_tau21 = open_files_muon(file, 'jetAK8_tau21')[trigger]
    jetAK8_eta = open_files_muon( file , 'jetAK8_eta')[trigger]
    jetAK8_px = open_files_muon(file,'jetAK8_px')[trigger]
    jetAK8_py =  open_files_muon(file,'jetAK8_py')[trigger]
    jetAK8_pz =  open_files_muon(file,'jetAK8_pz')[trigger]
    jetAK8_E = open_files_muon(file,'jetAK8_E')[trigger]
    
    print('jetAK8_pt -->' , jetAK8_pt)

        
    METPt  = open_files_muon(file, 'METPt' )[trigger]
    METPx  = open_files_muon(file, 'METPx' )[trigger]
    METPy  = open_files_muon(file, 'METPy' )[trigger]
    METphi = open_files_muon(file, 'METphi')[trigger]

    print('METphi -->' ,METphi)

    muon_pt  = open_files_muon(file, 'muon_pt')[trigger]
    muon_eta = open_files_muon(file, 'muon_eta')[trigger]
    muon_phi = open_files_muon(file, 'muon_phi')[trigger]
    muon_px  = open_files_muon(file,'muon_px')[trigger]
    muon_py  = open_files_muon(file,'muon_py')[trigger]
    muon_pz  = open_files_muon(file,'muon_pz')[trigger]
    muon_E   = open_files_muon(file,'muon_E')[trigger]
    
    print( 'Muon_pt --> ', muon_pt )	
    
    k = ( ( Mw**2 ) / 2 + muon_px * METPx ) +  (muon_py * METPy ) 
    raiz_ = ( ( ( (k * muon_pz)**2) / (muon_pt**4)  - ( (muon_E * METPt)**2 - k) / muon_pt**2)**0.5 )    
    raiz = np.nan_to_num(raiz_) # Os valores de NaN, causados pela divisão por 0 ou pelo resultado de uma raiz imaginária, é substituida por NaN
    Pz_nu = ( ( k * muon_pz / (muon_pt**2 ) ) + raiz ) # coordenada z do momentum do neutrino reconstruido
    W_lep_energy = ( muon_E + (METPx**2 + METPy**2 + Pz_nu**2)**0.5) # Energia do par de léptons  


    print( 'energia do W leptonico -->', W_lep_energy ) 

  

    # Usamos o TLorenctzVector do Python 
    TLV_lep = uproot_methods.TLorentzVectorArray(
              muon_px + METPx,
              muon_py + METPy,
              muon_pz + Pz_nu, 
              W_lep_energy) # 4-vector do par de lepton
            
    TLV_jet = uproot_methods.TLorentzVectorArray(
              jetAK8_px,
              jetAK8_py,
              jetAK8_pz,
              jetAK8_E )    
    
    W_mass = ( TLV_lep + TLV_jet ).mass # Massa invariante do WW
    W_lep_pt = ( TLV_lep ).pt # Pt do par de lepton
    
    print( 'Massa W -->', W_mass )

    dphi_jet_lep = TLV_lep.phi - TLV_jet.phi
    dphi_jet_lep = np.where( dphi_jet_lep >=  scipy.constants.pi, dphi_jet_lep - 2*scipy.constants.pi, dphi_jet_lep)
    dphi_jet_lep = np.where( dphi_jet_lep <  - scipy.constants.pi, dphi_jet_lep + 2*scipy.constants.pi, dphi_jet_lep) # delta phi entre o jato e o par de lepton
    dphi_jet_MET = METphi - TLV_jet.phi
    dphi_jet_MET = np.where( dphi_jet_MET >=  scipy.constants.pi, dphi_jet_MET - 2*scipy.constants.pi, dphi_jet_MET)
    dphi_jet_MET = np.where( dphi_jet_MET <  - scipy.constants.pi, dphi_jet_MET + 2*scipy.constants.pi, dphi_jet_MET) # delta phi entre o jato e o MET 
    

    '''
    ** numeração das colunas do numpy array ** ( para facilitar na hora de fazer os cortes )

    0  --> massa do WW
    1  --> Pt do W leptônico
    2  --> DeltaPhi entre W_hadrônico e W_leptônico
    3  --> DeltaPhi entre Jatos e o MET
    4  --> jetAK8_pt
    5  --> jetAK8_eta
    6  --> jetAK8_prunedMass
    7  --> jetAK8_tau21
    8  --> METPt
    9  --> muon_pt
    10 --> muon_eta
    11 --> ExtraTracks

    '''

    
    pfeta = open_files_PF( file, 'pfeta' )[trigger]
    pfphi = open_files_PF( file, 'pfphi' ) [trigger]
    pffromPV = open_files_PF( file, 'pffromPV' )[trigger]
   
    dR_muon = ( ( pfeta - muon_eta )**2 + ( pfphi - muon_phi )**2 )**0.5
    dR_jet =  ( ( pfeta - TLV_jet.eta )**2 + ( pfphi - TLV_jet.phi )**2 )**0.5 
    
    print( 'dR_muon' , dR_muon )

    dR_muon = dR_muon[pffromPV == 3]
    dR_jet = dR_jet[pffromPV == 3]  
    
    dR_jet = dR_jet[dR_muon > 0.3]

    dR_jet = dR_jet[dR_jet > 0.8]
    
    ExtraTracks = [len(arr) for arr in dR_jet]
    
    ExtraTracks = np.array(ExtraTracks).reshape(-1,1)
        
    print('Tracos Extras -->' , ExtraTracks )

    events_all = np.concatenate( ( W_mass.reshape(-1,1), W_lep_pt.reshape(-1,1), dphi_jet_lep.reshape(-1,1), 
    dphi_jet_MET.reshape(-1,1), jetAK8_pt.reshape(-1,1), TLV_jet.eta.reshape(-1,1), jetAK8_prunedMass.reshape(-1,1), jetAK8_tau21.reshape(-1,1), METPt.reshape(-1,1), muon_pt.reshape(-1,1), muon_eta.reshape(-1,1), ExtraTracks) , axis = 1 ) # concatenando todos as variáveis

    events_all_cut = (events_all[:,4] >= 200) & (events_all[:,5] <= 2.4) & (events_all[:,8] >= 40)  & (events_all[:,9] >= 53)  & (events_all[:,10] <= 2.4)  # realizando os cortes nas variáveis
    
    array_numpy = events_all[events_all_cut]  

    #columns = ['Mww','Pt_W_lep','dPhi_Whad_Wlep','dPhi_jatos_MET','jetAK8_pt','jetAK8_eta','jetAK8_prunedMass','jetAK8_tau21','METPt','muon_pt','muon_eta','ExtraTracks']

    #DataFrame = pd.DataFrame( array_numpy , columns = columns )

    print( 'array completo --> ', array_numpy )	

    #return DataFrame # ou retorna o DataFrame com as colunas 
    return array_numpy # ou retorna um matriz numpy aninhada para economizar memória



