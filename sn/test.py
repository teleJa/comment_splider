# -*- coding: utf-8 -*-
# @author: Tele
# @Time  : 2019/04/15 下午 10:17
import re
test = "//review.suning.com/cluster_cmmdty_review/general-30259269-000000010748901691-0000000000-1-total.htm?originalCmmdtyType=general"
res = re.findall("general-(.*?)-",test)

print(res[0])