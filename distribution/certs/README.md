Note: If you are on Windows, execute these commands under git bash (or any system supporting POSIX openssl).

`certs.rar` includes a sample certificate and private key.

---

1. Generate a self-signed certificate:

```sh
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout private_key.pem -out cert.pem -addext "subjectAltName = DNS:distribution"
```
Note: You can omit the `-addext "subjectAltName = DNS:distribution"` option, but in that case, make sure to set the Common Name (CN) to distribution. This is necessary to enable proper SSL communication between the backend and the distribution container.

2. We'll also need the base64 certificate payload (that is, without the headers). For that purpose, we can convert `.pem` into `.der` and then convert the binary `.der` into base64:

```sh
openssl x509 -in cert.pem -outform der -out cert.der
base64 cert.der > cert.der.b64
rm cert.der
```