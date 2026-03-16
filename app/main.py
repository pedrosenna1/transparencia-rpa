from fastapi import FastAPI,status,Request,HTTPException,Depends
from typing import Dict
from app.schemas.main import Dados,Search
from app.rq import queue
from app.automation import act
from rq import Retry
from rq.job import Job, JobStatus
from app.rq import redis
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime,timedelta,timezone

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

load_dotenv()

app = FastAPI()

def check_jwt(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não é possivel validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token,key=os.getenv("JWT_KEY"),algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return {
        'username': username
    }




@app.post('/token')
async def token(form: OAuth2PasswordRequestForm = Depends()):
    if form.username == os.getenv('USERNAME') and form.password == os.getenv('SENHA'):
        try:
           token =  jwt.encode({
                'sub': form.username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=1)
            },key=os.getenv("JWT_KEY"),algorithm="HS256")
        except:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Erro ao gerar Token.')
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Credenciais incorretas.')
    
    return {
        'access_token': token,
        'token_type': "bearer"
    }




@app.post('/search',status_code=status.HTTP_200_OK,response_model=Dict,summary='Realiza uma busca no portal da transparência e retorna os dados encontrados',dependencies=[Depends(check_jwt)])
async def search(search: Search):
    try:
        if search.filtro_busca:
            job = queue.enqueue(act,str(search.search),str(search.filtro_busca))
            
        else:
            job = queue.enqueue(act,str(search.search))
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='Não foi possivel realizar a automação')
    
    return {
        'status': 'Success',
        'id': job.id
    }

@app.get('/result/{job_id}',status_code=status.HTTP_200_OK,response_model=Dados,dependencies=[Depends(check_jwt)])
async def result(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis)
        job.refresh()
    except Exception:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    if job.get_status() == JobStatus.FAILED:
        error = job.latest_result().exc_string.strip().split('\n')[-1]
        return {
            "status": "failed",
            "id": job_id,
            "error": error 
        }
    
    if not job.is_finished:
        return {'status': 'pending', 'id': job_id}


    
    return {'status': 'Success', 'result': job.result}