
次 2 つの機能を提供します。

- GitHub Webhook の POST データを S3 へ保存。
- Public レポジトリ作成時、またはレポジトリの可視性を Public に変更された場合、メール通知。


## アーキテクチャ図
![architecture](./assets/architecture.drawio.svg)


## 前提条件
- Webhook POST データ保存先 S3 バケットの作成

- API Gateway ログ記録用ロールの設定

  (参考: https://docs.aws.amazon.com/ja_jp/apigateway/latest/developerguide/set-up-logging.html#set-up-access-logging-permissions)

- Referer 用のランダム文字列の生成

- GitHub Webhook 用の Secret 生成

備考: Python で安全なランダム文字列を生成するワンライナー
```bash
python -c 'import secrets; print(secrets.token_hex(64))'
```


## 構成手順


#### 1. API Gateway 以降構成用のパラメタ設定

./config/cfn_param_template.json の次キーへ値を入力してください。

- RefererValue: API GW へのアクセスを CloudFront に限定するための Referer にセットするランダム値
- BucketName:  Webhook POST データ保存先 S3 バケット (KDF 出力先)


#### 2. API Gateway 以降の構成

次コマンドを参考に CFn スタックを作成してください。アーキテクチャ図 API Gateway 以降のリソースが展開されます。

```bash
mkdir ./cfn/.build/

aws cloudformation package \
    --template-file ./cfn/github-webhook.cfn.yml \
    --s3-bucket ${YOUR_S3_BUCKET_NAME_FOR_CFN} \
    --output-template-file ./cfn/.build/github-webhook.packed.cfn.yml \
    --region ${YOUR_AWS_REGION} \
    --profile ${YOUR_AWS_PROFILE}

aws cloudformation deploy \
    --template ./cfn/.build/github-webhook.packed.cfn.yml \
    --stack-name github-webhook \
    --parameter-overrides file://./config/cfn_param_template.json \
    --capabilities CAPABILITY_IAM \
    --region ${YOUR_AWS_REGION} \
    --profile ${YOUR_AWS_PROFILE}
```

必要に応じて、SNS トピック: github-webhook-notification-publicized を購読してください。Public レポジトリ検出時に通知されます。


#### 3. POST ハッシュ値検証用 Lambda のパラメタ登録

GitHub Webhook Secret と API Gateway API キーを Parameter Store へ登録します。
次コマンドを参考に設定してください。

```bash
aws ssm put-parameter \
    --name /github/webhook/secret-token/default \
    --type SecureString \
    --value ${GITHUB_WEBHOOK_SECRET_TOKEN} \
    --region us-east-1 \
    --profile ${YOUR_AWS_PROFILE}

aws ssm put-parameter \
    --name /github/webhook/apigw-apikey/default \
    --type SecureString \
    --value ${APIGW_API_KEY} \
    --region us-east-1 \
    --profile ${YOUR_AWS_PROFILE}
```

API キーは API Gateway の AWS コンソールより API キー名: github-ApiAp-[CFn より生成されるランダムな文字列] から取得してください。


#### 4. 検証機能構成用のパラメタ設定

./config/cfn_param_template.json のキー DomainName の値に手順 2. で作成された API Gateway のドメイン名を入力してください。


#### 5. 検証機能構成

次のコマンドを実行してください。POST 検証用の CloudFront と Lambda@Edge が展開されます。

```bash
aws cloudformation package \
    --template-file ./cfn/github-webhook-validating.cfn.yml \
    --s3-bucket ${YOUR_S3_BUCKET_NAME_FOR_CFN_CF_REGION} \
    --output-template-file ./cfn/.build/github-webhook-validating.packed.cfn.yml \
    --region us-east-1 \
    --profile ${YOUR_AWS_PROFILE}

aws cloudformation deploy \
    --template ./cfn/.build/github-webhook-validating.packed.cfn.yml \
    --stack-name github-webhook-validating \
    --parameter-overrides file://./config/cfn_param_template.json \
    --capabilities CAPABILITY_IAM \
    --region us-east-1 \
    --profile ${YOUR_AWS_PROFILE}
```


#### 6. GitHub Webhokk 設定

GitHub の Webhooks / Manage webhook 設定画面より、
Payload URL へ https://[5. で作成された CloudFront ディストリビューションドメイン名]/prod を、
Secret へシークレット値を入力して Webhook の作成を行ってください。
