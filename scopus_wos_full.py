import requests
import math
import pandas as pd
import sys
import time

list_of_scopus = []
medical_jif_scopus = "medical_jif_scopus_authors_5-9.xlsx"
medical_jif_jif = "medical_jif_scopus_authors_5-9.xlsx"
medical_jif_final = "medical_jif_scopus_authors_5-9.xlsx"
scopus_api_key = '123'
wos_api_key = '456'
um_affiliations = ['60021519', '60017287', '60004546', '60122645', '60009932', '60122646', '60016686', '60020817', '60122645', '60011479', '60017510']
# issn jif jifYear jifCategory jifRank creator title journal {year;volume;issue;pages doi. pubmedId aggregationType affiliation
journal_dict = {'issn': None,
                'eIssn': None,
                'jif': None,
                'jifYear': None,
                'jifCategory': None,
                'jifRank': None,
                'creator': None,
                'authors': None,
                'umAuthors': None,
                'nonUMAuthors': None,
                'title': None,
                'journal': None,
                'date': None,
                'year': None,
                'volume': None,
                'issue': None,
                'pages': None,
                'doi': None,
                'pubmedId': None,
                'aggregationType': None,
                'umAffiliation': None,
                'nonUMAff': None,
                'amaCitation': None
                }


def formatted_issn(issn):
    # converts 12345678 to 1234-5678
    if issn and len(issn) == 8:
        issn = issn[:4] + '-' + issn[4:]
    return issn


def format_citation():
    output_string = "IF: {jif} ({jifYear}). {authors} {title}. {journal}. {year};{volume}({issue}):{pages}. {doi}."
    df = pd.read_excel(medical_jif_jif)
    for index, journal in df.iterrows():
        citation = output_string.format(jif=journal['jif'],
                                        jifYear=journal['jifYear'],
                                        jifCategory=journal['jifCategory'],
                                        jifRank=journal['jifRank'],
                                        authors=journal['authors'],
                                        title=journal['title'],
                                        journal=journal['journal'],
                                        year=journal['year'],
                                        volume=journal['volume'],
                                        issue=journal['issue'],
                                        pages=journal['pages'],
                                        doi=journal['doi']
                                        )
        print(citation)
        df.at[index, ' amaCitation'] = citation
        # print(journal)
        df.to_excel(medical_jif_final, index=False)


def export_to_excel(data):
    # convert array into dataframe
    df = pd.DataFrame(data=data)
    # save the dataframe as a xlsx file
    df.to_excel(medical_jif_scopus, index=False)


def export_to_csv(data):
    df = pd.DataFrame(data)

    # save the dataframe as a csv file
    df.to_csv("citations.csv", index=False)


def get_scopus_search_api(start):
    scopus_url = 'https://api.elsevier.com/content/search/scopus'

    headers = {
        'accept': 'application/json',
        'X-ELS-APIKey': scopus_api_key
    }
    params = {'query': '( AF-ID ( "University of Miami Leonard M. Miller School of Medicine" 60021519 )  )  AND PUBYEAR = 2023',
              # 'facets': 'authname',
              'view': 'COMPLETE',
              'start': start
              }

    # send request
    # print("*********SCOPUS RESPONSE*********")
    response = requests.get(scopus_url, headers=headers, params=params)
    # print(response.url)
    # print(response.text)
    # print(response.status_code)
    if response.status_code == 200:
        json_response = response.json()
        try:
            response = json_response['search-results']
        except KeyError:
            print(json_response)
            print("No Search Results, also check VPN connection")
            sys.exit(1)
        return response
    else:
        print(response.text)
        print(response.status_code)
        sys.exit(1)


def get_scopus_author_api(author_id):
    time.sleep(1)

    scopus_url = 'https://api.elsevier.com/content/author/author_id/{author_id}'.format(author_id=author_id)

    headers = {
        'accept': 'application/json',
        'X-ELS-APIKey': scopus_api_key
    }
    params = {
        'view': 'LIGHT'
    }

    # send request
    print("*********SCOPUS AUTHOR RESPONSE*********")
    response = requests.get(scopus_url, headers=headers, params=params)
    print(response.url)
    print(response.text)
    # print(response.status_code)
    json_response = response.json()
    department = ""
    try:
        author_results = json_response['author-retrieval-response']
        department = author_results[0].get("affiliation-current").get("affiliation-name")
    except KeyError:
        print("No Author Search Results for above")
    return department


def get_wos_api():
    wos_url = 'https://api.clarivate.com/apis/wos-journals/v1/journals'

    headers = {
        'Accept': 'application/json',
        'X-ApiKey': wos_api_key
    }
    scopus_excel_df = pd.read_excel(medical_jif_scopus)
    total = len(scopus_excel_df)

    #for index, row in scopus_excel_df.iloc[:5].iterrows():
    for index, row in scopus_excel_df.iterrows():
        count = index + 1
        print("getting wos " + str(count) + " out of " + str(total))
        #print(type(row['eIssn']))
        #print(row['eIssn'])
        pub_year = row['year']
        jcr_year = pub_year
        jif_found = False
        wos_journal = {}
        while not jif_found:
            if not pd.isna(row['eIssn']):
                print("*********** WOS - eIssn " + str(row['eIssn']) + " for " + str(jcr_year) + " **************")
                while not jif_found and int(jcr_year) >= 2022:
                    print(" no results. trying year " + str(jcr_year))
                    params = {
                        'q': row['eIssn'],
                        'jcrYear': jcr_year,
                        'jif': 'gte:0',
                        'jifPercentile': 'gte:0',
                        'jifQuartile': 'Q1;Q2;Q3;Q4'
                    }

                    # send request
                    response = requests.get(wos_url, headers=headers, params=params)
                    wos_journal = response.json()
                    if wos_journal['metadata']['total'] > 0:
                        jif_found = True
                        continue
                    else:
                        jcr_year = str(int(jcr_year) - 1)


            # If there are no results, search the issn
            if not pd.isna(row['issn']):
                jcr_year = pub_year
                print("*********** WOS - issn " + str(row['issn']) + " for " + str(jcr_year) + " **************")
                while not jif_found and int(jcr_year) >= 2022:
                    print(" no results. trying year " + str(jcr_year))
                    params = {
                        'q': row['issn'],
                        'jcrYear': jcr_year,
                        'jif': 'gte:0',
                        'jifPercentile': 'gte:0',
                        'jifQuartile': 'Q1;Q2;Q3;Q4'
                    }

                    # send request
                    response = requests.get(wos_url, headers=headers, params=params)
                    wos_journal = response.json()
                    if wos_journal['metadata']['total'] > 0:
                        jif_found = True
                        break
                    else:
                        jcr_year = str(int(jcr_year) - 1)

            print(wos_journal)

            if not jif_found:
                break

        if wos_journal['hits']:
            # print(wos_journal['hits'][0]['metrics']['impactMetrics']['jif'])
            print(wos_journal['hits'][0])
            try:
                #row.update({'jif': wos_journal['hits'][0]['metrics']['impactMetrics']['jif']})
                #row.update({'jifYear': wos_journal['hits'][0]['journalCitationReports'][0]['year']})
                #row.update({'jifCategory': wos_journal['hits'][0]['ranks']['jif'][0]['category']})
                #rank = wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")
                #row.update({'jifRank': rank[0]})
                scopus_excel_df.at[index, 'jif'] = wos_journal['hits'][0]['metrics']['impactMetrics']['jif']
                scopus_excel_df.at[index, 'jifYear'] = wos_journal['hits'][0]['journalCitationReports'][0]['year']
                scopus_excel_df.at[index, 'jifCategory'] = wos_journal['hits'][0]['ranks']['jif'][0]['category']
                scopus_excel_df.at[index, 'jifRank'] = wos_journal['hits'][0]['ranks']['jif'][0]['rank'].split("/")[0]
            except KeyError:
                continue
            except IndexError:
                continue

        # print(journal)
        time.sleep(1)

    return scopus_excel_df


def append_scopus_results(results):
    for journal in results:
        print(journal)
        current_title = journal_dict.copy()
        if 'prism:eIssn' in journal:
            current_title.update({'eIssn': formatted_issn(journal.get('prism:eIssn'))})
        if 'prism:issn' in journal:
            current_title.update({'issn': formatted_issn(journal.get('prism:issn'))})
        if 'dc:creator' in journal:
            current_title.update({'creator': journal.get('dc:creator')})
        if 'author' in journal:
            authors = []
            um_authors = []
            non_um_authors = []
            non_um_aff = []
            for author in journal.get("author"):
                authors.append(author.get("authname"))
                if 'afid' in author:
                    affiliated = False
                    for affiliation in author.get('afid'):
                        if affiliation.get('$') in um_affiliations:
                            #No department call for testing
                            #department = get_scopus_author_api(author.get("authid"))
                            department = ""
                            if department:
                                um_authors.append(author.get("authname") + " (" + department + ")")
                            else:
                                um_authors.append(author.get("authname"))
                            affiliated = True
                            break
                    if not affiliated:
                        non_um_authors.append(author.get("authname"))
                        non_um_aff.append(author.get("afid")[0].get("$"))
                else:
                    non_um_authors.append(author.get("authname"))

            current_title.update({'umAuthors': ', '.join(um_authors)})
            current_title.update({'nonUMAuthors': ', '.join(non_um_authors)})
            current_title.update({'nonUMAff': ', '.join(non_um_aff)})
            current_title.update({'authors': ', '.join(authors)})

        if 'dc:title' in journal:
            current_title.update({'title': journal.get('dc:title')})
        if 'prism:publicationName' in journal:
            current_title.update({'journal': journal.get('prism:publicationName')})
        if 'prism:coverDate' in journal:
            current_title.update({'date': journal.get('prism:coverDate')})
            current_title.update({'year': journal.get('prism:coverDate')[:4]})
        if 'prism:volume' in journal:
            current_title.update({'volume': journal.get('prism:volume')})
        if 'prism:issueIdentifier' in journal:
            current_title.update({'issue': journal.get('prism:issueIdentifier')})
        if 'prism:pageRange' in journal:
            current_title.update({'pages': journal.get('prism:pageRange')})
        if 'prism:doi' in journal:
            current_title.update({'doi': journal.get('prism:doi')})
        if 'pubmed-id' in journal:
            current_title.update({'pubmedId': journal.get('pubmed-id')})
        if 'prism:aggregationType' in journal:
            current_title.update({'aggregationType': journal.get('prism:aggregationType')})
        if 'affiliation' in journal:
            current_um_aff = []
            for affiliation in journal.get('affiliation'):
                if affiliation.get("afid") in um_affiliations:
                    current_um_aff.append(affiliation.get("affilname"))
            current_title.update({'umAffiliation': ','.join(current_um_aff)})

        # print(current_title)
        list_of_scopus.append(current_title)


if __name__ == "__main__":
    start = 0
    scopus_search_results = get_scopus_search_api(start)
    pages = math.ceil(int(scopus_search_results['opensearch:totalResults']) / 25)
    current_page = 1
    while current_page <= pages:
    ##while current_page == 1:
       print("getting page " + str(current_page) + " out of " + str(pages))
       scopus_search_results = get_scopus_search_api(start)
       append_scopus_results(scopus_search_results['entry'])
       current_page += 1
       start += 25

    export_to_excel(list_of_scopus)
    current_df = pd.read_excel(medical_jif_scopus)
    current_df.fillna(value="")
    print("CURRENT_DF")
    print(current_df)
    df_with_jif = get_wos_api()
    print("writing jif")
    df_with_jif.to_excel(medical_jif_jif, index=False)
    print("writing citation")
    format_citation()
    export_to_csv(citations)
    export_to_excel(df_with_jif)
