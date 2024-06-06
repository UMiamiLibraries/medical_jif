import pandas as pd


def format_citation(jif_df):
    for index, pub in jif_df.iterrows():
        citation = ""
        if not pd.isna(pub['jif']):
            citation = f"IF: {pub['jif']} ({pub['jifYear']}). "

        if not pd.isna(pub['volume']) and not pd.isna(pub['pages']) and not pd.isna(pub['issue']):
            citation = citation + f"{pub['authors']} {pub['title']}. {pub['journal']}. " \
                       f"{pub['year']};{pub['volume']}({pub['issue']}):{str(pub['pages'])}."
        elif not pd.isna(pub['volume']) and pd.isna(pub['issue']) and pd.isna(pub['pages']):
            citation = citation + f"{pub['authors']} {pub['title']}. {pub['journal']}. " \
                       f"{pub['year']};{pub['volume']}."
        elif pd.isna(pub['volume']) and pd.isna(pub['issue']) and not pd.isna(pub['pages']):
            citation = citation + f"{pub['authors']} {pub['title']}. {pub['journal']}. " \
                       f"{pub['year']}:{pub['pages']}."
        elif not pd.isna(pub['volume']) and not pd.isna(pub['issue']) and pd.isna(pub['pages']):
            citation = citation + f"{pub['authors']} {pub['title']}. {pub['journal']}. " \
                       f"{pub['year']};{pub['volume']}({pub['issue']})."
        else:
            citation = citation + f"{pub['authors']} {pub['title']}. {pub['journal']}. " \
                   f"{pub['year']};{pub['volume']}."

        if not pd.isna(pub['doi']):
            citation = citation + " " + pub['doi']
        #print(citation)
        jif_df.at[index, 'amaCitation'] = citation

    return jif_df


if __name__ == "__main__":
    jif_file = '../medical_jif_jifs_authors_5-9.xlsx'
    results_file = '../medical_jif_results_authors_5-9.xlsx'

    jif_df = pd.read_excel(jif_file)
    jif_df.fillna(value="")

    print("Formatting Citations...")
    jif_df = format_citation(jif_df)
    jif_df.to_excel(results_file, index=False)
