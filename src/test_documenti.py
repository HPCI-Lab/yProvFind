from elasticsearch import AsyncElasticsearch
import asyncio

async def main():
    es = AsyncElasticsearch(
        hosts="https://localhost:9200",
        basic_auth=("elastic", "3_rc51nu6W0lGEf*Mj-P"),
        verify_certs=False
    )
    print("connesso")
    resp = await es.search(index="documents", query={"match_all": {}})
    for hit in resp["hits"]["hits"]:
        print(hit["_source"])

    print("Totale documenti indicizzati:", resp["hits"]["total"]["value"])



    await es.close()

asyncio.run(main())
