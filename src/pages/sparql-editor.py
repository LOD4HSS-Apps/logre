import pandas as pd
from code_editor import code_editor
import streamlit as st
import lib.state as state
from components.init import init
from components.menu import menu
from dialogs import dialog_queries_save, dialog_queries_load



##### The page #####

init(layout='wide')
menu()

# From state
endpoint = state.get_endpoint()
data_bundle = state.get_data_bundle()

# Can't make a SPARQL query if there is no endpoint
if not endpoint:

    st.title("SPARQL Editor")
    st.text('')
    st.warning('You need to select an endpoint first (menu on the left).')

else:

    graph_begin = "GRAPH " + endpoint.sparql.prepare_uri(data_bundle.graph_data.uri) + " {" if data_bundle and data_bundle.graph_data.uri else ""
    graph_end = "}\n" if data_bundle and data_bundle.graph_data.uri else "\n"

    default_query = """        
SELECT ?s ?p ?o
WHERE {
    """ + graph_begin + """
        ?s ?p ?o .
    """ + graph_end + """
}
LIMIT 10
    """.strip()


    # Title and load query option
    col1, col2 = st.columns([12, 3], vertical_alignment='bottom')
    col1.title("SPARQL Editor")
    col2.button('Load saved queries', on_click=dialog_queries_load, icon=':material/list:')

    # Display prefixes for user to know
    prefixes_str = '`, `'.join(['`base`'] + [p.short for p in endpoint.sparql.get_prefixes()])
    st.markdown('Available prefixes are: `' + prefixes_str + '`')

    # Code editor
    sparql_query = code_editor(
        lang="sparql",
        code=default_query,
        height="400px",
        buttons=[{"name": "Run SPARQL Query", "hasText": True, "alwaysOn": True,"style": {"top": "350px", "right": "0.4rem"}, "commands": ["submit"]}]
    )

    st.text("")

    # When the user executes via the inbox button
    if sparql_query['type'] == 'submit':

        # Run (ie query or execute) the query
        result = endpoint.sparql.run(sparql_query['text'])

        # Clear cache, because user might have inserted/deleted/updated data that needs to be refetched
        st.cache_data.clear()
        st.cache_resource.clear()
    
        # If there is a result, display result and options:
        #       Option1: Save the query that gave this result
        #       Option2: Download the dataframe as a CSV
        if isinstance(result, list):
            result_df = pd.DataFrame(data=result)
            
            # Option line
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2], vertical_alignment='bottom')
            col1.markdown("### Response")
            col2.markdown(f"Shape: {result_df.shape[0]}x{result_df.shape[1]}")
            col3.download_button('Download CSV', data=result_df.to_csv(index=False), file_name="logre-download.csv", mime="text/csv", icon=':material/download:')
            col4.button('Save query', on_click=dialog_queries_save, kwargs={'text': sparql_query['text']}, icon=':material/reorder:')
            
            # The result itself
            st.dataframe(result_df, use_container_width=True, hide_index=True)

        else:
            # In case the query was an insert or a delete, display a message to inform user
            state.set_toast('Query executed', icon=':material/done:')