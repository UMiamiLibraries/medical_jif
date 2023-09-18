import requests
import pandas as pd
import time

wos_api_key = '123'


def format_citation(jif_df):
    for index, pub in jif_df.iterrows():
        if not pd.isna(pub['JIF']):
            citation = f"IF: {pub['JIF']} ({pub['JIFYear']}). {pub['Authors']} {pub['Title']}. {pub['Source title']}. " \
                       f"{pub['Year']};{pub['Volume']}({pub['Issue']}):{str(pub['Page start'])}-{str(pub['Page end'])}. {pub['DOI']}."
        else:
            citation = f"{pub['Authors']} {pub['Title']}. {pub['Source title']}. " \
                       f"{pub['Year']};{pub['Volume']}({pub['Issue']}):{str(pub['Page start'])}-{str(pub['Page end'])}. {pub['DOI']}."
        print(citation)
        jif_df.at[index, 'amaCitation'] = citation

    return jif_df


# methods are 1 - jif_ranks and 2 - jif_only
def wos_api(method, issn, year):
    print("*********** WOS - ISSN " + issn + " for " + str(year) + " **************")
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

    for index, row in scopus_excel_df.iterrows():
        count = index + 1
        print("getting row " + str(count) + " out of " + str(total))
        if not pd.isna(row['ISSN']):
            if row['ISSN'] in processed_jifs:
                print("pulling " + row['ISSN'] + " data from processed_jifs")
                scopus_excel_df.at[index, 'JIF'] = processed_jifs[row['ISSN']].get('jif')
                scopus_excel_df.at[index, 'JIFYear'] = processed_jifs[row['ISSN']].get('jifyear')
                scopus_excel_df.at[index, 'JIFCategory'] = processed_jifs[row['ISSN']].get('jifcategory')
                scopus_excel_df.at[index, 'JIFRank'] = processed_jifs[row['ISSN']].get('jifrank')
            else:
                wos_journal = wos_api(1, row['ISSN'], '2022')

                if wos_journal['hits']:
                    try:
                        scopus_excel_df.at[index, 'JIF'] = wos_journal['hits'][0]['metrics']['impactMetrics']['jif']
                        scopus_excel_df.at[index, 'JIFYear'] = str(wos_journal['hits'][0]['journalCitationReports'][0]['year'])
                        scopus_excel_df.at[index, 'JIFCategory'] = wos_journal['hits'][0]['ranks']['jif'][0]['category']
                        scopus_excel_df.at[index, 'JIFRank'] = wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")[0]
                        processed_jifs[row['ISSN']] = {
                            'jif': wos_journal['hits'][0]['metrics']['impactMetrics']['jif'],
                            'jifyear': str(wos_journal['hits'][0]['journalCitationReports'][0]['year']),
                            'jifcategory': wos_journal['hits'][0]['ranks']['jif'][0]['category'],
                            'jifrank': wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")[0]
                        }
                    except KeyError:
                        continue
                    except IndexError:
                        continue
                else:
                    wos_journal = wos_api(2, row['ISSN'], '2022')
                    if wos_journal['hits']:
                        try:
                            scopus_excel_df.at[index, 'JIF'] = wos_journal['hits'][0]['metrics']['impactMetrics']['jif']
                            scopus_excel_df.at[index, 'JIFYear'] = wos_journal['hits'][0]['journalCitationReports'][0]['year']
                            scopus_excel_df.at[index, 'JIFCategory'] = ""
                            scopus_excel_df.at[index, 'JIFRank'] = ""
                            processed_jifs[row['ISSN2']] = {
                                'jif': wos_journal['hits'][0]['metrics']['impactMetrics']['jif'],
                                'jifyear': wos_journal['hits'][0]['journalCitationReports'][0]['year'],
                                'jifcategory': "",
                                'jifrank': ""
                            }
                        except KeyError:
                            continue
                        except IndexError:
                            continue

                time.sleep(1)

    return scopus_excel_df


if __name__ == "__main__":
    scopus_file = 'scopus_file_with_issns.xlsx'
    results_file = 'wos_jif_final.xlsx'

    print("Reading Scopus File...")
    jif_df = pd.read_excel(scopus_file)
    jif_df.fillna(value="")

    print("Starting WOS Process...")
    jif_df = process_wos_data(jif_df)
    jif_df.to_excel(results_file, index=False)

    print("Formatting Citations...")
    jif_df = format_citation(jif_df)
    jif_df.to_excel(results_file, index=False)
