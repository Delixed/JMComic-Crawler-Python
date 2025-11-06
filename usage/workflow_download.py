from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
1036723
1040326
1051122
620673
1051117
1048728
640480
616523
1054588
1054820
575802
530503
497723
273098
205181
191787
188627
152604
1059011
526450
616326
1059257
1058178
1061972
1063432
1065052
1074213
1074744
524148
473454
438513
1079727
1085401
1082840
1039903
565661
444904
1087326
1092062
571926
1092955
1094899
1096582
575798
594130
596940
1088221
1099087
1055336
1107768
1084741
1124922
1132644
1144533
1151613
458045
1173128
553957
1173130
1158343
1173705
1180603
1186545
1189002
1074429
1191813
1197384
1174457
1092952
1198446
1199694
1193773
1194533
1194856
1187681
1195176
1195164
1196755
1195433
541246
248285
297100
348112
535887
574308
1029352
1200355
1202016
1202344
611836
1202538
1202601
1203558
1203789
1204715
1205544
1205555
1205551
1206643
1206646
1206668
1207086
525566
622386
1117339
644781
82692
103016
103105
147714
1125669
1209520
1212311
531549
1212661
1212890
1213425
1214303
1214511
1214565
1215066
1215195
1134580
543557
1215607
1215814
1215981
1217821
1217114
1218356
1141352
1093864
1058705
1018931
596434
567015
560697
549296
535272
527505
1218497
1099101
544009
473107
313478
1219498
1220199
1221666
1210176
1020220
639800
1221842
1221964
1222394
1223980
1224867
1225249
1225198
1225329
1225855
1213848
1226545


'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
