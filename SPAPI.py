import os,sys,time
from dotenv import load_dotenv
import hashlib
import requests
import hmac
import urllib.parse
import requests
import json
from time import gmtime, strftime
import datetime
import pandas as pd

# .envファイルの内容を読み込みます
load_dotenv()

# os.environを用いて環境変数を表示させます
# REFRESH_TOKEN= os.environ['REFRESH_TOKEN']
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET= os.environ['CLIENT_SECRET']
ACCESS_KEY=os.environ['ACCESS_KEY']
SECRET_KEY=os.environ['SECRET_KEY']

#REFRESH_TOKEN= os.environ['REFRESH_TOKEN']
# CLIENT_ID = "amzn1.application-oa2-client.59f360bdd9064965bcddef537ada1ecd"
# CLIENT_SECRET= "aa9026ec8373a5e2ce8487d2f9d945432549aa7f88467533dfc6cb094555436a"
# ACCESS_KEY="AKIARB5KAK2F4POHOO5I"
# SECRET_KEY="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"

#refresh_token = REFRESH_TOKEN
client_id=CLIENT_ID
client_secret=CLIENT_SECRET
access_key = ACCESS_KEY
secret_key = SECRET_KEY
marketplaceIds="A1VC38T7YXB528"

def getAccessToken(refresh_token):
    url = "https://api.amazon.com/auth/o2/token"

    payload='grant_type=refresh_token&refresh_token='+refresh_token+'&client_id='+client_id+'&client_secret='+client_secret
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    jsonData=response.json()

    access_token=jsonData["access_token"]
 
    return access_token


def SPAPI_GetCompetitivePricing(Asin_Code, SPAPI_Access_Token, SPAPI_IAM_User_Access_Key, SPAPI_IAM_User_Secret_Key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent):
#    SPAPI_API_Path = '/catalog/2022-04-01/items'
#    request_parameters_unencode = {
#        'identifiers' : Asin_Code,
#        'identifiersType' : 'ASIN',
#        'includedData' : 'attributes,dimensions,salesRanks',
#        'marketplaceIds' : str(SPAPI_MarketplaceId),
#    } 
    
    SPAPI_API_Path = '/products/pricing/v0/competitivePrice'
    request_parameters_unencode = {
        'Asins' : Asin_Code,
        'ItemType' : 'Asin',
        'MarketplaceId' : str(SPAPI_MarketplaceId),
    }     
    
    request_parameters = urllib.parse.urlencode(request_parameters_unencode)
    ### Python による署名キーの取得関数
    ## 参考：http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, 'aws4_request')
        return kSigning
    ### ヘッダー情報と問合せ資格(credential)情報のための時刻情報作成
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
    
    ### =================================================================================
    ### Canonical Request の作成
    ### 参考：http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
    ### =================================================================================

    ## URI設定
    canonical_uri = SPAPI_API_Path

    ## 正規リクエストパラメータ設定
    canonical_querystring = request_parameters

    ## 正規リクエストヘッダリストの作成
    canonical_headers = 'host:' + SPAPI_Domain + '\n' + 'user-agent:' + SPAPI_UserAgent + '\n' + 'x-amz-access-token:' + SPAPI_Access_Token + '\n' + 'x-amz-date:' + amzdate + '\n'

    ## 正規リクエストヘッダリストの項目情報の作成(hostとx-amz-dateも入れてる)
    signed_headers = 'host;user-agent;x-amz-access-token;x-amz-date'

    ## ペイロードハッシュ（リクエスト本文コンテンツのハッシュ）の作成
    ## ※GETリクエストの場合、ペイロードは空の文字列（""）になる。
    payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

    ## 正規リクエストの作成
    canonical_request = SPAPI_Method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    ## 問合せ資格情報を作成し、署名方式、ハッシュ化された正規リクエスト情報を結合した情報を作成する
    credential_scope = datestamp + '/' + SPAPI_Region + '/' + SPAPI_Service + '/' + 'aws4_request'
    string_to_sign = SPAPI_SignatureMethod + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    ## 定義した関数を用いて署名鍵を作成
    signing_key = getSignatureKey(SPAPI_IAM_User_Secret_Key, datestamp, SPAPI_Region, SPAPI_Service)

    ## 署名鍵で、上記で作成した「string_to_sign」に署名
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    ## Authorizationヘッダの作成
    authorization_header = SPAPI_SignatureMethod + ' ' + 'Credential=' + SPAPI_IAM_User_Access_Key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    ## API問合せ用ヘッダ情報の作成
    headers = {'user-agent':SPAPI_UserAgent, 'x-amz-access-token':SPAPI_Access_Token, 'x-amz-date':amzdate, 'Authorization':authorization_header}

    ## APIリクエストURLの作成
    request_url = SPAPI_Endpoint + canonical_uri + '?' + request_parameters

    ### ====================
    ### SP-APIリクエスト
    ### ====================
#    print('=== Request ===')
#    print('Request URL = ' + request_url)
    api_response = requests.get(request_url, headers=headers)

    return getDictAndASINs_fromGetCompetitivePricing(json.loads(api_response.text), Asin_Code)


def getDictAndASINs_fromGetCompetitivePricing(api_response, code_list):
 #   print("code_list="+code_list)
    codes=code_list.split(',')

    codes_dict={}
    for code in codes:
        codes_dict[code]=""

    codes_dict=dict.fromkeys(codes)
        
 #   print(api_response.text)
 #   print('\n')
    asins=[]
    for item in api_response['payload']:
        data={}
        
        #ASIN
        asin=item['ASIN']
        asins.append(asin)
        #その他(ASIN,JANも含む)
        other=item

        data['asin']=asin
        
        data['info']=other
        codes_dict[asin]=data
        
    return codes_dict, asins






def SPAPI_GetCatalogItems(Code_Type, Code, SPAPI_Access_Token, SPAPI_IAM_User_Access_Key, SPAPI_IAM_User_Secret_Key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent):
    SPAPI_API_Path = '/catalog/2022-04-01/items'
    request_parameters_unencode = {
        'identifiers' : Code,
        'identifiersType' : Code_Type,
        'includedData' : 'attributes,dimensions,salesRanks,images',
        'marketplaceIds' : str(SPAPI_MarketplaceId),
    } 
    request_parameters = urllib.parse.urlencode(request_parameters_unencode)
    ### Python による署名キーの取得関数
    ## 参考：http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, 'aws4_request')
        return kSigning
    ### ヘッダー情報と問合せ資格(credential)情報のための時刻情報作成
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
    
    ### =================================================================================
    ### Canonical Request の作成
    ### 参考：http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
    ### =================================================================================

    ## URI設定
    canonical_uri = SPAPI_API_Path

    ## 正規リクエストパラメータ設定
    canonical_querystring = request_parameters

    ## 正規リクエストヘッダリストの作成
    canonical_headers = 'host:' + SPAPI_Domain + '\n' + 'user-agent:' + SPAPI_UserAgent + '\n' + 'x-amz-access-token:' + SPAPI_Access_Token + '\n' + 'x-amz-date:' + amzdate + '\n'

    ## 正規リクエストヘッダリストの項目情報の作成(hostとx-amz-dateも入れてる)
    signed_headers = 'host;user-agent;x-amz-access-token;x-amz-date'

    ## ペイロードハッシュ（リクエスト本文コンテンツのハッシュ）の作成
    ## ※GETリクエストの場合、ペイロードは空の文字列（""）になる。
    payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

    ## 正規リクエストの作成
    canonical_request = SPAPI_Method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    ## 問合せ資格情報を作成し、署名方式、ハッシュ化された正規リクエスト情報を結合した情報を作成する
    credential_scope = datestamp + '/' + SPAPI_Region + '/' + SPAPI_Service + '/' + 'aws4_request'
    string_to_sign = SPAPI_SignatureMethod + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    ## 定義した関数を用いて署名鍵を作成
    signing_key = getSignatureKey(SPAPI_IAM_User_Secret_Key, datestamp, SPAPI_Region, SPAPI_Service)

    ## 署名鍵で、上記で作成した「string_to_sign」に署名
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    ## Authorizationヘッダの作成
    authorization_header = SPAPI_SignatureMethod + ' ' + 'Credential=' + SPAPI_IAM_User_Access_Key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    ## API問合せ用ヘッダ情報の作成
    headers = {'user-agent':SPAPI_UserAgent, 'x-amz-access-token':SPAPI_Access_Token, 'x-amz-date':amzdate, 'Authorization':authorization_header}

    ## APIリクエストURLの作成
    request_url = SPAPI_Endpoint + canonical_uri + '?' + request_parameters

    ### ====================
    ### SP-APIリクエスト
    ### ====================
 #   print('=== Request ===')
 #   print('Request URL = ' + request_url)
    api_response = requests.get(request_url, headers=headers)

    #return json.loads(api_response.text)
    return getDictAndASINs_fromGetCatalogItems(Code_Type, json.loads(api_response.text), Code)


def getDictAndASINs_fromGetCatalogItems(code_type, api_response, code_list):
    #print("code_list="+code_list)
    codes=code_list.split(',')

    codes_dict={}
    for code in codes:
        codes_dict[code]=""

    codes_dict=dict.fromkeys(codes)
        
 #   print(api_response.text)
 #   print('\n')
    asins=[]
    jans=[]
    for item in api_response['items']:
        data={}
        
        #ASIN
        asin=item['asin']
        asins.append(asin)
        #JAN
        jan=item['attributes']['externally_assigned_product_identifier'][0]['value']
        jans.append(jan)
        #その他(ASIN,JANも含む)
        other=item

        data['asin']=asin
        data['jan']=jan
        data['info']=other

        if code_type=="ASIN":
            codes_dict[asin]=data
        else:
            codes_dict[jan]=data

    return codes_dict, asins, jans




def SPAPI_BatchesProductsPricingItemOffers(Asin_Code, SPAPI_Access_Token, SPAPI_IAM_User_Access_Key, SPAPI_IAM_User_Secret_Key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent):
    SPAPI_API_Path = '/batches/products/pricing/v0/itemOffers'
    request_parameters_unencode = {} 
    request_parameters = urllib.parse.urlencode(request_parameters_unencode)
    
    requests_list=[]
    for asin in Asin_Code.split(','):
        request_dict={}
        request_dict['uri'] = "/products/pricing/v0/items/" + asin + "/offers"
        request_dict['method'] = "GET"
        request_dict['MarketplaceId'] = SPAPI_MarketplaceId
        request_dict['ItemCondition'] = "New"
        request_dict['CustomerType'] = "Consumer"
        requests_list.append(request_dict)
    
    payload_dict={}
    payload_dict['requests']=requests_list
    payload = json.dumps(payload_dict)

    
    ### Python による署名キーの取得関数
    ## 参考：http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, 'aws4_request')
        return kSigning
    ### ヘッダー情報と問合せ資格(credential)情報のための時刻情報作成
    t = datetime.datetime.utcnow()
    amzdate = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
    
    ### =================================================================================
    ### Canonical Request の作成
    ### 参考：http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
    ### =================================================================================

    ## URI設定
    canonical_uri = SPAPI_API_Path

    ## 正規リクエストパラメータ設定
    canonical_querystring = request_parameters

    ## 正規リクエストヘッダリストの作成
    canonical_headers = 'host:' + SPAPI_Domain + '\n' + 'user-agent:' + SPAPI_UserAgent + '\n' + 'x-amz-access-token:' + SPAPI_Access_Token + '\n' + 'x-amz-date:' + amzdate + '\n'

    ## 正規リクエストヘッダリストの項目情報の作成(hostとx-amz-dateも入れてる)
    signed_headers = 'host;user-agent;x-amz-access-token;x-amz-date'

    ## ペイロードハッシュ（リクエスト本文コンテンツのハッシュ）の作成
    ## ※GETリクエストの場合、ペイロードは空の文字列（""）になる。
#    payload_hash = hashlib.sha256(request_parameters.encode('utf-8')).hexdigest()
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    ## 正規リクエストの作成
    canonical_request = SPAPI_Method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    ## 問合せ資格情報を作成し、署名方式、ハッシュ化された正規リクエスト情報を結合した情報を作成する
    credential_scope = datestamp + '/' + SPAPI_Region + '/' + SPAPI_Service + '/' + 'aws4_request'
    string_to_sign = SPAPI_SignatureMethod + '\n' +  amzdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    ## 定義した関数を用いて署名鍵を作成
    signing_key = getSignatureKey(SPAPI_IAM_User_Secret_Key, datestamp, SPAPI_Region, SPAPI_Service)

    ## 署名鍵で、上記で作成した「string_to_sign」に署名
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    ## Authorizationヘッダの作成
    authorization_header = SPAPI_SignatureMethod + ' ' + 'Credential=' + SPAPI_IAM_User_Access_Key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    ## API問合せ用ヘッダ情報の作成
    headers = {'user-agent':SPAPI_UserAgent, 'x-amz-access-token':SPAPI_Access_Token, 'x-amz-date':amzdate, 'Authorization':authorization_header,'Content-Type': 'application/json'}

    ## APIリクエストURLの作成
#    request_url = SPAPI_Endpoint + canonical_uri + '?' + request_parameters
    request_url = SPAPI_Endpoint + canonical_uri +  request_parameters

    ### ====================
    ### SP-APIリクエスト
    ### ====================
    #print('=== Request ===')
    #print('Request URL = ' + request_url)
    api_response = requests.post(request_url, headers=headers,data=payload)

    #return json.loads(api_response.text)
    #return api_response

    #print(api_response.text)
    ret=getDictAndASINs_fromBatchesProductsPricingItemOffers(json.loads(api_response.text), Asin_Code)
    return ret



def getDictAndASINs_fromBatchesProductsPricingItemOffers(api_response, code_list):
 #   print("code_list="+code_list)
    codes=code_list.split(',')

    codes_dict={}
    for code in codes:
        codes_dict[code]=""

    codes_dict=dict.fromkeys(codes)

    asins=[]
    for response in api_response['responses']:
        #正常に取得できた場合
        if checkExists('payload',response['body']):
            item=response['body']['payload']
            data={}
            
            #ASIN
            asin=item['ASIN']
            asins.append(asin)
            #その他(ASIN,JANも含む)
            other=item

            data['asin']=asin
            
            data['info']=other
            codes_dict[asin]=data
        #else:
            #何もしない

    return codes_dict, asins




def getDictFromAPI(code_type, input_codes_str, refresh_token):
    access_token=getAccessToken(refresh_token)
    SPAPI_Method="GET"
    SPAPI_Service ="execute-api"
    SPAPI_Domain = "sellingpartnerapi-fe.amazon.com"
    SPAPI_MarketplaceId = marketplaceIds
    SPAPI_Region = "us-west-2"
    SPAPI_Endpoint = "https://sellingpartnerapi-fe.amazon.com"
    SPAPI_SignatureMethod ="AWS4-HMAC-SHA256"
    SPAPI_UserAgent ="SPAPI-App"

    #code_type="JAN"

    data1,asins1,jans =SPAPI_GetCatalogItems(code_type,input_codes_str, access_token, access_key, secret_key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent)
#    data2,asins2=SPAPI_GetCompetitivePricing(",".join(asins1), access_token, access_key, secret_key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent)
#    print(asins1)
    SPAPI_Method="POST"
    data2,asins2 =SPAPI_BatchesProductsPricingItemOffers(",".join(asins1), access_token, access_key, secret_key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent)


#    SPAPI_Method="POST"
#    api_response,asins =SPAPI_BatchesProductsPricingItemOffers(",".join(asins1), access_token, access_key, secret_key, SPAPI_Method, SPAPI_Service, SPAPI_Domain, SPAPI_MarketplaceId, SPAPI_Region, SPAPI_Endpoint, SPAPI_SignatureMethod, SPAPI_UserAgent)

 
    #print(data2)
    #print(asins2)
    input_codes=input_codes_str.split(',')
    response_data={}
    for code in input_codes:
        #APIで取得したdata1に取得したいJAN又はASINの情報が含まれている場合
        if code_type=="JAN":
            api_codes= jans
        else:
            api_codes=asins1

        data={}
        if code in api_codes:
            data['data1']=data1[code]
            asin=data1[code]['asin']
            data['data2']=data2[asin]
            response_data[code]=data

        else:
            response_data[code]=None

    return response_data
    #print(data1)

def extractData(api_data):
    data_dict={}
    #print("#############################")
    for code in api_data.keys():
        row_dict={}
        row_dict[code]=code
        tmp=api_data[code]
        if not api_data[code] is None:
#           print(str(api_data[code]['data1']))
            row_dict['ASIN']=api_data[code]['data1']['asin']
            row_dict['JAN']=api_data[code]['data1']['jan']
            row_dict['タイトル']=api_data[code]['data1']['info']['attributes']['item_name'][0]['value']

            if checkExists('manufacturer',api_data[code]['data1']['info']['attributes']):
                row_dict['出版社・メーカー']=api_data[code]['data1']['info']['attributes']['manufacturer'][0]['value']

            if checkExists('list_price',api_data[code]['data1']['info']['attributes']):
                row_dict['定価']=api_data[code]['data1']['info']['attributes']['list_price'][0]['value']

            if checkExists('part_number',api_data[code]['data1']['info']['attributes']):
                row_dict['型番']=api_data[code]['data1']['info']['attributes']['part_number'][0]['value']
            elif checkExists('brand',api_data[code]['data1']['info']['attributes']):
                row_dict['型番']=api_data[code]['data1']['info']['attributes']['brand'][0]['value']

            if checkExists('height',api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]):
                row_dict['高さ']=api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]['height']['value']

            if checkExists('length',api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]):
                row_dict['長さ']=api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]['length']['value']
 
            if checkExists('width',api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]):
                row_dict['幅']=api_data[code]['data1']['info']['attributes']['item_package_dimensions'][0]['width']['value']

            if checkExists('item_package_weight',api_data[code]['data1']['info']['attributes']):
                row_dict['重さ']=api_data[code]['data1']['info']['attributes']['item_package_weight'][0]['value']

            #ClassificationRanks
            if checkExists('salesRanks',api_data[code]['data1']['info']):
                if checkExists('classificationRanks',api_data[code]['data1']['info']['salesRanks'][0]):
                    row_dict['ランキング名1']=api_data[code]['data1']['info']['salesRanks'][0]['classificationRanks'][0]['title']
                    row_dict['ランキング1']=api_data[code]['data1']['info']['salesRanks'][0]['classificationRanks'][0]['rank']

            #DisplayGroupRanks
            if checkExists('salesRanks',api_data[code]['data1']['info']):
                if checkExists('displayGroupRanks',api_data[code]['data1']['info']['salesRanks'][0]):
                    row_dict['ランキング名2']=api_data[code]['data1']['info']['salesRanks'][0]['displayGroupRanks'][0]['title']
                    row_dict['ランキング2']=api_data[code]['data1']['info']['salesRanks'][0]['displayGroupRanks'][0]['rank']

            if checkExists('images',api_data[code]['data1']['info']):
                if checkExists('images',api_data[code]['data1']['info']['images'][0]):
                    row_dict['画像']=api_data[code]['data1']['info']['images'][0]['images'][0]['link']

            ###################
            #BatchesProductsPricingItemOffers
            ###################
            print("####"+code)
            row_dict['BuyBox価格']='-'
            row_dict['BuyBox送料']='-'
            row_dict['BuyBoxポイント']='-'
            #BuyBox(Buyboxが存在して新品がないときは[0]にusedがくる)
            if checkExists('BuyBoxPrices',api_data[code]['data2']['info']['Summary']):
                if checkExists('ListingPrice',api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]):
                    row_dict['BuyBox価格']=api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]['ListingPrice']['Amount']
                if checkExists('Shipping',api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]):                
                    row_dict['BuyBox送料']=api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]['Shipping']['Amount']
                if checkExists('Points',api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]):
                    row_dict['BuyBoxポイント']=api_data[code]['data2']['info']['Summary']['BuyBoxPrices'][0]['Points']['PointsNumber']



            #出品者数
            row_dict['Amazon新品数']="-"
            row_dict['Merchant新品数']="-"
            row_dict['Amazon中古数']="-"
            row_dict['Merchant中古数']="-"
            if checkExists('BuyBoxEligibleOffers',api_data[code]['data2']['info']['Summary']):
                for offer in api_data[code]['data2']['info']['Summary']['BuyBoxEligibleOffers']:
                    if offer['condition']=='new' and offer['fulfillmentChannel']=='Amazon':
                        row_dict['Amazon新品数']=offer['OfferCount']
                    elif offer['condition']=='new' and offer['fulfillmentChannel']=='Merchant':
                        row_dict['Merchant新品数']=offer['OfferCount']
                    elif offer['condition']=='used' and offer['fulfillmentChannel']=='Amazon':
                        row_dict['Amazon中古数']=offer['OfferCount']
                    elif offer['condition']=='used' and offer['fulfillmentChannel']=='Merchant':
                        row_dict['Merchant中古数']=offer['OfferCount']
            '最安値'
            row_dict['Amazon新品最安値']="-"
            row_dict['Amazon新品送料']="-"
            row_dict['Amazon新品ポイント']="-"
            row_dict['Merchant新品最安値']="-"
            row_dict['Merchant新品送料']="-"
            row_dict['Merchant新品ポイント']="-"
            row_dict['Amazon中古最安値']="-"
            row_dict['Amazon中古送料']="-"
            row_dict['Amazon中古ポイント']="-"
            row_dict['Merchant中古最安値']="-"
            row_dict['Merchant中古送料']="-"
            row_dict['Merchant中古ポイント']="-"
            if checkExists('LowestPrices',api_data[code]['data2']['info']['Summary']):
                for offer in api_data[code]['data2']['info']['Summary']['LowestPrices']:
                    if offer['condition']=='new' and offer['fulfillmentChannel']=='Amazon':
                        key="Amazon"+"新品"
                    elif offer['condition']=='new' and offer['fulfillmentChannel']=='Merchant':
                        key="Merchant"+"新品"
                    elif offer['condition']=='used' and offer['fulfillmentChannel']=='Amazon':
                        key="Amazon"+"中古"
                    elif offer['condition']=='used' and offer['fulfillmentChannel']=='Merchant':
                        key="Merchant"+"中古"

                        row_dict[key + '最安値']=offer['ListingPrice']['Amount']
                        if checkExists('Shipping',api_data[code]['data2']['info']['Summary']):
                            row_dict[key + '送料']=offer['Shipping']['Amount']
                        if checkExists('Points',api_data[code]['data2']['info']['Summary']):
                            row_dict[key + 'ポイント']=offer['Points']['PointsNumber']

            print(str(row_dict))
#        else:
#            print('NONE')
        data_dict[code]=row_dict
    
    return data_dict

def checkExists(key,dic):
    if not dic.get(key) is None:
        if len(dic.get(key))>0:
#        print(key+":true")
            return True
    else:
#        print(key+":false")
        return False
    


def main():

    refresh_token = REFRESH_TOKEN
   #identifiers="B07G9ZSJ8H,B09S3H736Q,B07BBL4XXX,B07BG7C8BG,B078YGQ125,B07BBL4RFP"
    input_codes_str="4902370539073,2200630036822,4902370538731,490237053876X,2200630036839,4902370538762"
    #input_codes_str="4902370539073"
    #input_codes_str="2200630036822,4902370538731,490237053876X"
    code_type='JAN'
    res=getDictFromAPI(code_type,input_codes_str, refresh_token)
    #test(refresh_token)
    #print(res)

    data_dict=extractData(res)
    print(data_dict)


if __name__ == "__main__":
    main()






