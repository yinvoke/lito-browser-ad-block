# Lito Browser Ad Block

Lito Browser 的广告拦截规则上游项目。定期同步第三方规则，并编译为 Lito 可直接加载的紧凑规则。

## 订阅地址

```text
https://yinvoke.github.io/lito-browser-ad-block/v1/
```

## 规则来源

| 类型 | 来源 | 采用版本 | 用途 |
|---|---|---|---|
| 网络 | AdGuard DNS filter | 官方 DNS 过滤器 | 广告与跟踪域名 |
| 网络 | HaGeZi Multi Pro | `adblock/pro.txt` | 广告与隐私保护 |
| 网络 | HaGeZi TIF | `adblock/tif.mini.txt` | 恶意软件、诈骗、垃圾邮件与钓鱼域名 |
| 网络 | anti-AD | `domains.txt` | 中文互联网广告域名补充 |
| 元素隐藏 | AdGuard Chinese | uBlock 格式 `224.txt` | 中文网页元素隐藏与路径例外 |

完整的上游地址和许可证信息见 [`sources.json`](sources.json) 与 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 发布内容

编译后的域名规则、网络例外、元素隐藏规则、来源信息及版本文件位于 [`public/v1`](public/v1)。Lito 通过 HTTPS 下载，并按发布清单校验版本、长度和 SHA-256 后热更新当前规则。

## 许可证

构建脚本采用 [GPL-3.0](LICENSE)。第三方规则继续遵循各自的许可证和署名条款。
