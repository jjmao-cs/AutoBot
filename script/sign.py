"""
ABOUT this code:
    "main" function:
        Description: sign in to human system in NCU and sign for part-time work
        NOTICE: for this function, the id and password must be correct. U can use "auth_check" to comfirm your information.
        Params:
            id: NCU student ID for portal
            password: NCU student password for portal
            job_description: For human system's part-time work sign description
    
    "auth_check" function:
        Description: can verify your portal login information.
        Params:
            id: NCU student ID for portal
            password: NCU student password for portal
"""


import requests
from lxml import html
from bs4 import BeautifulSoup as bs

#main sign core
def main(id,password,job_description):

    with requests.session() as session_requests:
        #parameters
        cookie=session_requests.get('https://portal.ncu.edu.tw')
        cookie=session_requests.cookies.get_dict() #cookie for NCU_Portal login
        User_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
        header={
            'User-Agent':User_agent,}
        log={
            '_csrf':cookie['XSRF-TOKEN'],
            'language':'ENGLISH',
            'username': id,
            'password': password}
        
        # <<login to NCU_Portal>>
        # we go straight to the login page and send the inform to the server to let session login
        result=session_requests.post(
            'https://portal.ncu.edu.tw/login',
            data=log,
            headers=header,
            cookies=cookie)

        result_bs = bs(result.text,'lxml')
        jump = session_requests.get('https://cis.ncu.edu.tw/HumanSys/student/stdSignIn')
        new_cookie = session_requests.cookies.get_dict()

        # Redirect from portal to human system by token given in portal (index) file
        token = ''
        for i in result_bs.findAll('script', type="text/javascript"):
            if 'var token = ' in i.string:
                    x = 'var token = "'
                    start = i.string.find(x) + len(x)
                    end = i.string.find('";',start)
                    token = i.string[start:end]
        human = session_requests.get('https://portal.ncu.edu.tw/system/142?token='+token,headers=header,cookies=new_cookie)

            
        # <<Enter HR System to get __token, ParttimeUsuallyId, idNo for each sign in/out>>
        # human = session_requests.get('https://cis.ncu.edu.tw/HumanSys/student/stdSignIn') # session_requests.get('https://portal.ncu.edu.tw/system/143')
        soup_human = bs(human.text, "lxml")
        #print(soup_human.find_all('a'))
        check='https://cis.ncu.edu.tw/HumanSys/student/'+soup_human.find_all('a')[-2].get('href') # url for the job's sign page
        sign=session_requests.get(check) # goto job's sign page
        soup_sign = bs(sign.text, "lxml") # through BeautifulSoup inorder to get some information
        sign_token = soup_sign.find_all("input")[0].get('value') # get the token used to protect the server of sign page
        ParttimeUsuallyId = soup_human.find_all('a')[-2].get('href').split("=")[-1] # ParttimeUsuallyId is an ID related to a person and its job
        idNo=soup_sign.find(id='idNo') 
            # idNo will be empty before sign in, 
            # the system will give client a idNo after sign in,
            # will be use when sign out.

        # <<Sign in and Sign out>>
        sign_data={
            'functionName' : "doSign",
            'idNo' : idNo['value'],
            'ParttimeUsuallyId' : ParttimeUsuallyId,
            'AttendWork' : job_description,
            '_token' : sign_token
        }
        sign_header = header.copy()

        # WARNING DO NOT REMOVE OR ADD THE PARA. BELOW. WILL CAUSE ERROR #THIS IS SOMETHING FOR TESTING
        #del sign_header['Referer']
        #sign_header['Host'] = 'https://cis.ncu.edu.tw'
        #print(sign.cookies.get_dict())
        # WARNING END #

        sign_post=session_requests.post(
            'https://cis.ncu.edu.tw/HumanSys/student/stdSignIn_detail',
            data = sign_data,
            headers = sign_header,
        )
        
        # used to make a GET to server, now seems USELESS
        # Research shows that sign in and out can be trigger by same content packet.
        '''data={'ParttimeUsuallyId' : ParttimeUsuallyId,
                'msg':'signin_ok'}
        sign_out_get=session_requests.get(
            'https://cis.ncu.edu.tw/HumanSys/student/stdSignIn/create?ParttimeUsuallyId=84668&msg=signout_ok',
            headers = sign_header,
            cookies = sign.cookies.get_dict()
        )
        #print(sign_out_post)
        #print(bs(sign_out_post.text, "lxml"))
        '''


def auth_check(id,password):
    with requests.session() as session_requests:
        #parameters
        cookie=session_requests.get('https://portal.ncu.edu.tw')
        cookie=session_requests.cookies.get_dict() #cookie for NCU_Portal login
        User_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
        header={
            'User-Agent':User_agent,}
        log={
            '_csrf':cookie['XSRF-TOKEN'],
            'language':'ENGLISH',
            'username': id,
            'password': password}
        result=session_requests.post(
            'https://portal.ncu.edu.tw/login',
            data=log,
            headers=header,
            cookies=cookie)

        if result.url == 'https://portal.ncu.edu.tw/':
            return True
        elif result.url == 'https://portal.ncu.edu.tw/login':
            return False
        else:
            print("[Error] Condition miss match at auth_check")
            return False