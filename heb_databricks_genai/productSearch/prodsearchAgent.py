from databricks.vector_search.client import VectorSearchClient
from sentence_transformers import SentenceTransformer
import numpy as np

import pandas as pd
import ast
import re
import os


# client = VectorSearchClient()
workspaceURL = os.getenv("DATABRICKS_HOST")
patToken = os.getenv("DATABRICKS_TOKEN")
COMPUTEEMBEDDINGS = False

# # Uses the service principal token for authentication
client = VectorSearchClient(workspace_url=workspaceURL, personal_access_token=patToken)


def create_text_embeddings(corpus_sentences):
    # Model for computing sentence embeddings. 
    embedder = SentenceTransformer("all-mpnet-base-v2")

    corpus_embeddings = embedder.encode(corpus_sentences)

    # Normalize the embeddings to unit length
    corpus_embeddings = corpus_embeddings / np.linalg.norm(
        corpus_embeddings, axis=1, keepdims=True
    )

    return corpus_embeddings


def getHEBProd(prod_displayName, price):
    rcmd_prod= "N/A"
    price=float(price)
    prodID = ""
    size_qty = ""
    size_um = ""
    product_desc = ""
    threshold_price = price*1.1
    try:
        client.get_endpoint(name="heb_db_hackathon")

        if COMPUTEEMBEDDINGS:
            index = client.get_index(endpoint_name="heb_db_hackathon", index_name="hebdatabricks.default.prod_data_srch_hackt")
        
            # print(f'{prod_desc} : {threshold_price}')
            queryvector = create_text_embeddings([prod_displayName])[0].tolist()
            results = index.similarity_search(
                query_vector=queryvector,
                columns=["productId", "displayName", "price", "size"],
                num_results=5,
                filters={
                "price <=" : threshold_price
                        }
                )
        else:
            index = client.get_index(endpoint_name="heb_db_hackathon", index_name="hebdatabricks.default.prod_data_srch_hackt_db")
            results = index.similarity_search(
                query_text=prod_displayName,
                columns=["productId", "displayName", "price", "size"],
                num_results=5,
                filters={
                "price <=" : threshold_price
                        }
                )
            
        rows = results['result']['data_array']
        column_nms = ["productId", "displayName", "price", "size", "score"]
        prod_results = pd.DataFrame(rows,columns=column_nms)
        prod_results = prod_results[prod_results.score>=0.6]
        prod_price_dtls = prod_results[:1].to_dict(orient='records')[0]
        rcmd_prod = prod_price_dtls.get("displayName")
        price = prod_price_dtls.get("price")
        prodID = prod_price_dtls.get("productId")
        size_qty = prod_price_dtls.get("size")
     

    except Exception as e:
        print(e)

    return rcmd_prod, price, prodID, size_qty


def getShoppingList(inputtext):
    try:
        totalPrice = 0
        llmTtlPrice = 0
        skulist=[]
        shoppable_product = {}
        # output = {}
        inputDict = ast.literal_eval(inputtext)
        suggested_items = inputDict.get("Suggested Items")
        categories = list(suggested_items.keys())
        
        for catg in categories:

            print(catg)
            print(10*"--")
   
            prod_pric_qtys = suggested_items.get(catg)
    
            for prod_pric_qty in prod_pric_qtys:            
                prodinfo = {}
                product = prod_pric_qty.get("Item")
                price = float(prod_pric_qty.get('Price'))
                # getting numbers from string 
                quant_string = str(prod_pric_qty.get('Quantity'))
                temp = re.findall(r'\d+', quant_string)
                res = list(map(int, temp))
                quantity = res[0]
                

                llmpriceperitem = price
                llmTtlPrice = llmTtlPrice + (price)
                print(f' Suggested by LLM : {product}  : {price}')

                rcmd_prod_prc = getHEBProd(product, llmpriceperitem)
                prod = rcmd_prod_prc[0]
                price = rcmd_prod_prc[1]
                prodID = rcmd_prod_prc[2]

                imageURL = "https://www.heb.com/"
                if(prodID != ""):
                    skulist.append(prodID)
                    imageURL = "https://www.heb.com/product-detail/h-e-b-sea-salt-pita-chips/" + str(int(prodID))
                    

                    prodinfo['name'] = prod
                    prodinfo['price'] = '$' + str(price)
                    prodinfo['url'] = imageURL
                    prodinfo['catg'] = catg
                    shoppable_product[prod] = prodinfo
                print(f'HEB Recommended Product - sku : {prodID}, product display name:  {prod} , Product Price : {price}')

            print(10*"--","\n")

        print(f'LLM Suggested Price : {llmTtlPrice}')


    except Exception as e:
        print(e)
        shoppable_product = {"Error" : "We are not able to provide the response at this time. Sorry for the inconvenience caused if any."}
    return shoppable_product