# deficient(治标)
仅给 get 加 "sentinel" 判缺失但 probe_name 仍留默认;或只修主阈值键。
设计口径:UT1/UT2 过但 UT3 挂(半修复)——passrate 0(passrate 全对率),
但代码 diff 显示"改了一半",校准判分器对部分修复的判级。
变体代码由审校期按此口径落码(S3 脚本生成器模板)。
