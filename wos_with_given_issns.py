import requests
import pandas as pd
import time

wos_api_key = '123'

# methods are 1 - jif_ranks and 2 - jif_only
def wos_api(method, issn, year):
    wos_url = 'https://api.clarivate.com/apis/wos-journals/v1/journals'

    headers = {
        'Accept': 'application/json',
        'X-ApiKey': wos_api_key
    }
    if method == 1:
        print("Trying for jif_ranks")
        params = {
            'q': issn,
            'jcrYear': year,
            'jif': 'gte:0',
            'jifPercentile': 'gte:0',
            'jifQuartile': 'Q1;Q2;Q3;Q4'
        }
    elif method == 2:
        print("Trying for jif_only")
        params = {
            'q': issn,
            'jcrYear': year,
            'jif': 'gte:0',
        }
    response = requests.get(wos_url, headers=headers, params=params)
    wos_journal = response.json()
    print(wos_journal)
    return wos_journal


def process_wos_data(scopus_excel_df):

    total = len(scopus_excel_df)
    processed_jifs = {}
    issn_value = 'eIssn'
    year_value = '2022'
    for index, row in scopus_excel_df.iterrows():
        count = index + 1
        if pd.isna(row['jif']):
            #if count < 10:
            if count % 50 == 0:
                print("SAVING...")
                jif_df.to_excel(jif_file, index=False)
            print("getting row " + str(count) + " out of " + str(total))
            if not pd.isna(row[issn_value]):
                current_issn = row[issn_value]
                if row[issn_value] in processed_jifs:
                    print("pulling " + current_issn + " data from processed_jifs")
                    scopus_excel_df.at[index, 'jif'] = processed_jifs[current_issn].get('jif')
                    scopus_excel_df.at[index, 'jifYear'] = processed_jifs[current_issn].get('jifYear')
                    scopus_excel_df.at[index, 'jifCategory'] = processed_jifs[current_issn].get('jifCategory')
                    scopus_excel_df.at[index, 'jifRank'] = processed_jifs[current_issn].get('jifRank')
                else:
                    print("*********** WOS - ISSN " + current_issn + " for " + str(year_value) + " **************")
                    wos_journal = wos_api(1, current_issn, year_value)

                    if wos_journal['hits']:
                        try:
                            scopus_excel_df.at[index, 'jif'] = wos_journal['hits'][0]['metrics']['impactMetrics']['jif']
                            scopus_excel_df.at[index, 'jifYear'] = str(wos_journal['hits'][0]['journalCitationReports'][0]['year'])
                            scopus_excel_df.at[index, 'jifCategory'] = wos_journal['hits'][0]['ranks']['jif'][0]['category']
                            scopus_excel_df.at[index, 'jifRank'] = wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")[0]
                            processed_jifs[current_issn] = {
                                'jif': wos_journal['hits'][0]['metrics']['impactMetrics']['jif'],
                                'jifYear': str(wos_journal['hits'][0]['journalCitationReports'][0]['year']),
                                'jifCategory': wos_journal['hits'][0]['ranks']['jif'][0]['category'],
                                'jifRank': wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")[0]
                            }
                        except KeyError:
                            continue
                        except IndexError:
                            continue
                    else:
                        wos_journal = wos_api(2, current_issn, year_value)
                        if wos_journal['hits']:
                            try:
                                scopus_excel_df.at[index, 'jif'] = wos_journal['hits'][0]['metrics']['impactMetrics']['jif']
                                scopus_excel_df.at[index, 'jifYear'] = wos_journal['hits'][0]['journalCitationReports'][0]['year']
                                scopus_excel_df.at[index, 'jifCategory'] = ""
                                scopus_excel_df.at[index, 'jifRank'] = ""
                                processed_jifs[row[issn_value]] = {
                                    'jif': wos_journal['hits'][0]['metrics']['impactMetrics']['jif'],
                                    'jifYear': wos_journal['hits'][0]['journalCitationReports'][0]['year'],
                                    'jifCategory': "",
                                    'jifRank': ""
                                }
                            except KeyError:
                                continue
                            except IndexError:
                                continue

                    time.sleep(1)

    return scopus_excel_df


if __name__ == "__main__":
    ##UPDATE THE JIF_YEAR AND FILE NAMES. FIRST RUN IT ON THE SCOPUS_FILE. RERUN THIS FILE WITH THE JIF_FILE YEAR BEFORE THAT TO GET MORE RESULTS
    scopus_file = '../medical_jif_scopus_authors_5-9.xlsx'
    jif_file = '../medical_jif_jifs_authors_5-9.xlsx'
    results_file = '../medical_jif_results_authors_5-9.xlsx'

    print("Reading Scopus File...")
    #USE SCOPUS_FILE FOR FIRST RUN. FOR SUBSEQUENT RUNS, USE JIF_FILE
    ##MAKE SURE TO RUN BOTH ISSN AND EISSN
    jif_df = pd.read_excel(jif_file)
    jif_df.fillna(value="")

    print("Starting WOS Process...")
    jif_df = process_wos_data(jif_df)
    jif_df.to_excel(jif_file, index=False)
