from fastapi import FastAPI
from pydantic import BaseModel
from SPAPI import getDictFromAPI,extractData
class Item(BaseModel):
    code_type: str
    refresh_token: str
    codes: str

app = FastAPI()

@app.post("/item/")
async def get_items(item: Item):

    code_type=item.code_type
    refresh_token = item.refresh_token
    input_codes_str=item.codes

    res=getDictFromAPI(code_type,input_codes_str, refresh_token)
    data_dict=extractData(res)    

    return data_dict

if __name__ == '__main__':
    main()