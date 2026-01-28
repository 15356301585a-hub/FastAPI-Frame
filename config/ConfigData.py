apiConfig = {
    'return':{  # 默认请求成功返回信息
        'code':200,
        'message':'请求成功',
        'result':None,
    },
    'logger':{
        'saveHeaders':False, # 是否打印请求头
        'isBackDay':True, # 是否根据天数来删除日志
        'backDays':30, # 保存日志文件的天数
        'log_dir':'logs', # 保存大文件目录
    }
}