
import numpy as np
import xarray as xa
import regex as re
import os,sys,glob
import datetime, calendar
from boltons import iterutils
import xarray as xa
import f90nml

def organiza_dados(pathM,anoi,anof,meses,regiao,tagarea,freq=None):
    if not isinstance(meses,list):
        if not isinstance(meses,np.ndarray):
            sys.exit('MESES DEVE SER UMA LISTA OU ARRAY. SAINDO***')
    slat   = [regiao[2],regiao[-1]]
    slon   = [regiao[0],regiao[1]]
    pmerge = sorted(glob.glob(f'{pathM}/*'))
    pi,pf  = 0,1
    for c,pm in enumerate(pmerge):
        if re.search(fr'{anoi}',pm):
            pi += c
        if re.search(fr'{anof}',pm):
            pf += c    
    pathMD = sorted(pmerge[pi:pf])
    for cm,ms in enumerate(meses):
        for ca,aM in enumerate(pathMD):
            ano = re.findall(r'20[0-9][0-9]',aM)[0]
            if not isinstance(freq,int):
                sys.exit('A FREQ DEVE SER UM NUMERO INTEIRO. SAINDO***')
            if freq != 10:
                if freq != 15:
                    if freq != 31:
                        sys.exit('FREQ DEVE SER 10, 15 OU 31. SAINDO***')

            ndias = calendar.monthrange(int(ano),int(ms))[1] + 1
            dias  = [datetime.date(int(ano),int(ms),dia).strftime('%Y%m%d') for dia in range(1,ndias)]
            divd  = iterutils.chunked(dias,freq)
            if len(divd[-1]) == 1:
                if freq==15:
                    divd[1] = divd[1]+divd[-1]
                    divd    = divd[:2]
                if freq==10:
                     divd[2] = divd[2]+divd[-1]
                     divd    = divd[:3]
            for cds,dias in enumerate(divd):
                if cds==0:
                    prcl = [[] for x in range(len(divd))]
                for dia in dias:
                    tagfl = f'{pathM}/{ano}/{ms}/*{dia}*.grib2'
                    fl = glob.glob(tagfl)
                    if len(fl)==0:
                        continue
                    fl   = fl[0]
                    grb  = xa.open_dataset(fl,engine='cfgrib',decode_timedelta=True)
                    grb  = grb.assign_coords(longitude=(((grb.longitude + 180) % 360) - 180))
                    grb  = grb.sel(longitude=slice(*slon),latitude=slice(*slat))
                    prec = grb['prec'].values
                    if cm==0 and ca==0:
                        nx,ny   = prec.shape
                        precmes = np.zeros((len(divd),len(meses),len(pathMD),nx,ny))
                        lat     = grb['latitude'][:]
                        lon     = grb['longitude'][:]
                        np.savetxt(f'latitude_merge_{tagarea}.txt',lat)
                        np.savetxt(f'longitude_merge_{tagarea}.txt',lon)
                    prcl[cds].append(prec)
                matriS   = np.stack(prcl[cds],axis=0)
                precmes[cds,cm,ca,:,:] = np.sum(matriS,axis=0)
                #print(precmes[cds,cm,ca,:,:].max())
            print(f'MES {ms} DO ANO {ano} LIDO: {tagarea}***')

    return precmes

def calc_dist(matri,quantis,tagarea):
    if not isinstance(quantis,list):
        if not isinstance(quantis,np.ndarray):
            sys.exit('QUANTIS DEVE SER UMA LISTA OU ARRAY. SAINDO***')
    freq  = matri.shape[0]
    nmes  = matri.shape[1]
    nx,ny = matri.shape[-2:]
    for cf in range(freq):
        matriAC = matri[cf,:,:,:,:]
        if cf==0:
            distPREC = np.zeros((nmes,len(quantis),nx,ny))
        for cq,q in enumerate(quantis):
            for cm in range(nmes):
                #for x in range(nx):
                    #for y in range(ny):
                distPREC[cm,cq,:,:] = np.quantile(matriAC[cm,:,:,:],q,axis=0)
            print(f'QUANTIL DE {q} CALCULADO')
        if freq==1:
            np.save(f'distri_MERGE_mensal_{tagarea}.npy',distPREC)
            print(f'distri_MERGE_mensal_{tagarea} ---> CRIADO***')
        elif freq==2:
            np.save(f'distri_MERGE_{cf+1}_quinzena_{tagarea}.npy',distPREC)
            print(f'distri_MERGE_{cf+1}_quinzena_{tagarea} ---> CRIADO***')
        elif freq==3:
            np.save(f'distri_MERGE_{cf+1}_decendio_{tagarea}.npy',distPREC)
            print(f'distri_MERGE_{cf+1}_decendio_{tagarea} ---> CRIADO***')

nml    = f90nml.read('merge_params.nml')
regnm  = 'reg_amazonia_bacia_amazonas'
regiao = nml['regis_pre'][regnm]
meses  = [str(x).zfill(2) for x in range(1,13)]
merge  = "C:\\Users\\gabriel.pereira\\OneDrive - CENSIPAM\\Documentos\\plataforma-meteorologia-censipam-front\\src\\assets\\dados\\MERGE\\Diario"
mtt    = organiza_dados(merge,2001,2020,meses,regiao,regnm,freq=10)
quants = [.15,.35,.65,.85]
calc_dist(mtt,quants,regnm)

