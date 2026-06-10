from config.ConfigData import apiConfig

errors = {

}

def R(code=apiConfig['return']['code'],message=apiConfig['return']['message'],result=apiConfig['return']['result']):
    errMessage = errors.get(str(code))
    if errMessage:
        message = errMessage
    return {'code':code,'message':message,'result':result}