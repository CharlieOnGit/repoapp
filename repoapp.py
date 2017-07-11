# bloodreport

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')
from pptx import Presentation
import cx_Oracle

# In order for the functions below to do their jobs properly, id_key_* must be put into the repoapp folder. 

# mergecasting (merhing disparate records into 1 dataframe and ensuring logical datatypes)

# path to phi
phi_path = r'J:\CancerInst\PatientInfo\BiorepositoryPHI'

def update_idkey():
	print('running...')
	id_key_p = pd.read_csv(phi_path + r'\id_key_p.csv')
	id_key_r = pd.read_csv(phi_path + r'\id_key_r.csv')
	id_key_b = pd.read_csv(phi_path + r'\id_key_b.csv')
	id_key_t = pd.read_csv(phi_path + r'\id_key_t.csv')

	id_key_p.loc[:,'DB'] = 'Prostate'
	id_key_r.loc[:,'DB'] = 'Renal'
	id_key_b.loc[:,'DB'] = 'Bladder'
	id_key_t.loc[:,'DB'] = 'Testicular'

	dfs = [id_key_p,
	      id_key_r,
	      id_key_b,
	      id_key_t]

	id_key = pd.concat(dfs)
	id_key.loc[:, 'PID'] = pd.to_numeric(id_key.loc[:, 'PID'])
	id_key.sort_values('PID')
	id_key.to_pickle(phi_path + r'\id_key.pickle')
	print('ID Key has been updated.')	
def update_byhandcrt():
	print('running...')

	id_key = pd.read_pickle(phi_path + r'\id_key.pickle')

	crt_excel = pd.ExcelFile(phi_path + r'\CRT.xlsx')

	rutt = crt_excel.parse(sheetname='Ruttenberg')
	urol = crt_excel.parse(sheetname='FPA Urology')
	rado = crt_excel.parse(sheetname='Rad Onc')

	rutt.loc[:, 'Clinic'] = 'Ruttenberg'
	urol.loc[:, 'Clinic'] = 'FPA Urology'
	rado.loc[:, 'Clinic'] = 'RadOnc'

	fields = ['PID', 'FirstName', 'LastName', 'InitialVisit', 'CancerType', 'ConsentToBiorepository', 'ConsentToBlood', 'MostRecentBlood', 'MedicalOncologist', 'ConsentedBy', 'Clinic']

	rutt = rutt.loc[:, fields]
	urol = urol.loc[:, fields]
	rado = rado.loc[:, fields]

	#crt_pre1 = pd.merge(rutt, urol, how='outer')
	#crt = pd.merge(crt_pre1, rado, how='outer')

	dfs = [rutt, urol, rado]
	crt = pd.concat(dfs)
	crt = crt.loc[:, fields]

	crt = crt.reset_index()
	crt.drop('index', axis=1, inplace=True)

	#drop those mystery nulls in radonc
	s1 = crt.loc[:, 'PID']
	mask = pd.notnull(s1)
	crt = crt.loc[mask,:]

	#to-numeric on code columns
	crt.loc[:, 'ConsentToBiorepository'] = pd.to_numeric(crt.loc[:, 'ConsentToBiorepository'])
	crt.loc[:, 'ConsentToBlood'] = pd.to_numeric(crt.loc[:, 'ConsentToBlood'])
	crt.loc[:, 'CancerType'] = pd.to_numeric(crt.loc[:, 'CancerType'])
	crt.loc[:, 'MedicalOncologist'] = pd.to_numeric(crt.loc[:, 'MedicalOncologist'])

	#convert cancer type
	s1 = crt.loc[:, 'CancerType']
	mask1 = s1 == 1
	mask2 = s1 == 2
	mask3 = s1 == 3
	mask4 = s1 == 4
	mask5 = s1 == 0
	crt.loc[mask1, 'CancerType'] = 'Prostate'
	crt.loc[mask2, 'CancerType'] = 'Renal'
	crt.loc[mask3, 'CancerType'] = 'Bladder'
	crt.loc[mask4, 'CancerType'] = 'Testicular'
	crt.loc[mask5, 'CancerType'] = 'Control'

	#convert consent to blood
	s1 = crt.loc[:, 'ConsentToBlood']
	mask1 = s1 == 1
	mask2 = s1 == 0
	crt.loc[mask1, 'ConsentToBlood'] = 'Yes'
	crt.loc[mask2, 'ConsentToBlood'] = 'No'

	#convert consent to biorepo
	s1 = crt.loc[:, 'ConsentToBiorepository']
	mask1 = s1 == 1
	mask2 = s1 == 2
	mask3 = s1 == 0
	mask4 = s1 == 3
	crt.loc[mask1, 'ConsentToBiorepository'] = 'Yes'
	crt.loc[mask2, 'ConsentToBiorepository'] = 'Re-Approach'
	crt.loc[mask3, 'ConsentToBiorepository'] = 'No'
	crt.loc[mask4, 'ConsentToBiorepository'] = 'No_SeeComment'

	#convert MedicalOncologist
	s1 = crt.loc[:, 'MedicalOncologist']
	mask1 = s1 == 1
	mask2 = s1 == 2
	mask3 = s1 == 3
	mask4 = s1 == 4
	crt.loc[mask1, 'MedicalOncologist'] = 'Oh'
	crt.loc[mask2, 'MedicalOncologist'] = 'Galsky'
	crt.loc[mask3, 'MedicalOncologist'] = 'Tsao'
	crt.loc[mask4, 'MedicalOncologist'] = 'Sfakianos'

	crt = crt.sort_values('InitialVisit')

	crt = pd.merge(crt, id_key.loc[:, ['PID', 'MRN']], how='left', on=['PID'])

	fields = ['PID', 'MRN', 'FirstName', 'LastName', 'InitialVisit', 'CancerType', 'ConsentToBiorepository', 'ConsentToBlood', 'MostRecentBlood', 'MedicalOncologist', 'ConsentedBy', 'Clinic']
	crt = crt[fields]

	#for column in crt.columns:
	#    print(column)
	#    if len(crt.groupby(column).size()) < 10:
	#        crt.groupby(column).size().plot(kind='bar')
	#        plt.show()
	#    print('\n')
	    
	crt.to_pickle(phi_path + r'\crt_casted.pickle')

	print('CRT has been updated.')
def update_byhand_aliquot():
	print('running...')

	id_key = pd.read_pickle(phi_path + r'\id_key.pickle')

	aliq_excel = pd.ExcelFile(phi_path + '\Aliquots.xlsm')

	dfs = []
	for sheet in aliq_excel.sheet_names:
	    df = aliq_excel.parse(sheetname=sheet)
	    df.loc[:, 'Box'] = str(sheet)
	    dfs.append(df)


	aliq = pd.concat(dfs)

	fields = ['PID', 'SpecimenID', 'DiseaseDB', 'CollectionDate', 'ProcessingType', 'Volume(mL)', 'DrawTime', 'FreezeTime', 'Position', 'Box', 'Processor', 'Comment:', 'Unnamed: 11']

	aliq = aliq.loc[:, fields]

	#aliq.loc[:, 'Draw time '] = aliq.loc[:, 'Draw time '].strptime('%Y-%m-%d')

	#drop null ids
	s1 = aliq.loc[:, 'PID']
	mask = pd.notnull(s1)
	aliq = aliq.loc[mask,:]

	aliq = aliq.reset_index()
	aliq.drop('index', axis=1, inplace=True)
	aliq = pd.merge(aliq, id_key.loc[:, ['PID', 'MRN', 'FirstName', 'LastName']], how='left', on=['PID'])




	fields = ['PID', 'MRN', 'FirstName', 'LastName', 'SpecimenID', 'DiseaseDB', 'CollectionDate', 'ProcessingType', 'Volume(mL)', 'DrawTime', 'FreezeTime', 'Position', 'Box', 'Processor', 'Comment:', 'Unnamed: 11']
	aliq = aliq.loc[:, fields]
	aliq.loc[:, 'MRN'] = aliq.loc[:, 'MRN'].astype('float64', inplace=True)


	#for column in aliq.columns:
	#    print(column)
	#    if len(aliq.groupby(column).size()) < 15:
	#        aliq.groupby(column).size().plot(kind='bar')
	#        plt.show()
	#    print('\n')
	    
	aliq.to_pickle(phi_path + r'\aliq_casted.pickle')

	print('Aliquot Info has been updated.')
#Get rid of records without collection dates
def update_erap_aliquot():
	print('running...')
	#Pull the data into csvs
	p = pd.read_csv(phi_path + r'\BloodDraws_P.csv')
	r = pd.read_csv(phi_path + r'\BloodDraws_R.csv')
	b = pd.read_csv(phi_path + r'\BloodDraws_B.csv')
	t = pd.read_csv(phi_path + r'\BloodDraws_T.csv')

	#concat all dfs
	dfs = [p, b, r, t]
	blood_draws = pd.concat(dfs); blood_draws.head()

	# first, make sure names for the above categories are normalized:  pax and pbmc
	blood_draws.loc[(blood_draws.ProcType == r'PBMC/DNA') | (blood_draws.ProcType == r'PBMCs'), 'ProcType'] = 'PBMC'
	blood_draws.loc[(blood_draws.ProcType == r'PAXgene') | (blood_draws.ProcType == r'RNA (Tempus or PAXgene)'), 'ProcType'] = 'PAX'

	# create dict with volume mappings.  Everything is expressed in mL here. This dict will be passed to mapping f(x)
	sample = ['Plasma', 'Serum', 'Whole Blood (for DNA)', 'PAX', 'PBMC']
	volume = [10, 6, 0, 2.5, 42]
	pairs = zip(sample, volume)
	mapping = dict(pairs)
	blood_draws.loc[:, 'VolumeDrawn'] = blood_draws.loc[:, 'ProcType'].map(arg=mapping)
	blood_draws = blood_draws.loc[:, ['PID', 'VID', 'SpID', 'CollectionDate', 'ProcType', 'VolumeDrawn']]
	blood_draws.CollectionDate = pd.to_datetime(blood_draws.CollectionDate)
	blood_draws.to_pickle(phi_path + r'\blood_draws.pickle')
	print('Blood draws info has been updated.')


def cast_dtypes(df, dd):
    for column in df.columns:
        s = df.loc[:, column]
        s = s.astype(dd[column])
        df.loc[:, column] = s
    return df
def update_fullpull_p():
	tables = ['p', 'd', 'v', 's']
	for table in tables:
		dtypes = pd.read_csv(phi_path + '\dd_p_' + table + '.csv')
		x = dtypes.Field.values
		y = dtypes.dtype.values
		dtypes = dict(zip(x,y))
		df = pd.read_csv(phi_path + r'\aanalys_p_' + table + '.csv')
		df = cast_dtypes(df, dtypes)
		df.to_pickle(phi_path + r'\aanalys_p_' + table + '_casted.pickle')
		print(table + ' casted succesfully')


def update_all():
	'''Depends upon the following docs:
	From erap, placed into repoapp folder:
	1) aanalys_p_p, d, v, and s
	2) BloodDraws_P, R, B, T
	3) id_key_p, r, b, t
	From J drive:
	4) Clinical Research Tracking
	5) Aliquot Info'''
	update_idkey()
	update_byhandcrt()
	update_byhand_aliquot()
	update_erap_aliquot()
	update_fullpull_p()
	print('you\'re all set ;)')

#blood reporting
def aliquot_info(ids, identifier):
    df = pd.read_pickle(phi_path + r'aliq_casted.pickle')
    df.sort_values(by=['PID', 'CollectionDate'], inplace=True)

    s1 = df.loc[:, identifier]
    mask1 = s1.isin(ids)
    df = df.loc[mask1]
    return df
def aliquot_summary(ids, identifier):
    df = pd.read_pickle(phi_path + r'aliq_casted.pickle')
    df.sort_values(by=['PID', 'CollectionDate'], inplace=True)

    #First, lets get rid of anything that's unavailable
    s1 = df.loc[:, 'Unnamed: 11']
    mask1 = -(s1.str.contains('Not Available') & pd.notnull(s1)) #need to handle for nulls
    blood_comp = df.loc[mask1]
    
    #Second, retain only records in our ids set
    s1 = df.loc[:, identifier]
    mask1 = s1.isin(ids)
    df = df.loc[mask1]

    #A clever implementation of the groupbypbject!
    df = df.groupby(['PID', 'MRN', 'FirstName', 'LastName', 'SpecimenID', 'CollectionDate', 'ProcessingType']).size().reset_index()
    df.rename(columns={df.columns[len(df.columns)-1]: 'AvailableAliquotsCount'}, inplace=True)
    
    return df

#meeting reports
###########

#GU_DM

# this needs work!!! Goal is to store teh query in a pandas df
def sql_gu(query):

    dsnStr = cx_Oracle.makedsn("SDWHODBQA01", "1521", "MSDWUSERS")
    user = raw_input('username: ')
    password = raw_input('password: ') 
    con = cx_Oracle.connect(user=user, password=password, dsn=dsnStr)
    cur = con.cursor()
    cur.execute(query)
    cols = []
    for i in range(0, len(cur.description)):
        cols.append(cur.description[i][0])
        
    data = cur.fetchall()
    for i in range(0,len(data)):
        data[i] = list(data[i])
    
    df = pd.DataFrame(data, columns=cols)
    
    return df
    cur.close()
    con.close()



