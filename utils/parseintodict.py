import asyncpg
import pandas as pd
from utils.timeparser import parse_time_to_seconds, parse_seconds_to_time

async def parseintodict(insert: Union[pd.DataFrame, list]) -> list[dict]:
    count_partnumber = 1
    new_dict = []

    match insert:
        case pd.DataFrame():
            iscollabquery = False
            isclaimsquery = False
            issongquery = False
            isartistquery = False
            isuserclaimsquery = False

            if "partnumber" in insert.columns and "offsetstart" in insert.columns and "offsetend" in insert.columns:
                for row in insert.itertuples(index=False):    
                    if row.rating not in range(1,6):
                        raise TypeError("One of your ratings is not between 1 or 5 stars")

                    new_dict.append(
                            {
                            "partnumber": count_partnumber,
                            "offsetstartseconds": await parse_time_to_seconds(row.offsetstart), 
                            "offsetendseconds": await parse_time_to_seconds(row.offsetend),
                            "offsetstarttime": None,
                            "offsetendtime": None,
                            "rating": row.rating
                            }
                        )
                    
                    count_partnumber += 1
            else:
                raise ValueError("Not a Parts DataFrame.")

        case list():
            if len(insert) == 0:
                raise ValueError("The list has no records.")

            iscollabquery = any(
                ("collabid" in record and "collabname" in record and "normalizedname" in record) for record in insert
            )

            isclaimsquery = any(
                ("collabid" in record and "partid" in record and "userid" in record and "status" in record and "backups" in record) for record in insert
            )

            isuserclaimsquery = any(
                ("collabid" in record and "partid" in record and "userid" in record and "claimstatus" in record and "claimtype" in record and "claimid" in record and "ratingatclaimtime" in record) for record in insert
            )

            issongquery = any(
                ("songid" in record and "songname" in record and "artistid" in record and "artistname" in record and "normalizedsongname" in record and "normalizedartistname" in record) for record in insert
            )

            isartistquery = any(
                ("songid" not in record and "songname" not in record and "artistid" in record and "artistname" in record and "normalizedname" in record) for record in insert
            )

            if iscollabquery:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")
                    
                    new_dict.append(
                        {
                            "collabid": row['collabid'],
                            "songid": row['songid'],
                            "collabname": row['collabname'], 
                            "normalizedname": row['normalizedname'],
                            "startdate": row['startdate'],
                            "finishdate": row['finishdate'],
                            "megacollabstatus": row['megacollabstatus'],
                            "seasontokensrequired": row['seasontokensrequired'],
                            "hosts": row['hosts'],
                            "category": row['category'],
                            "difficulty": row['difficulty'],
                            "stars": row['stars'],
                            "demondifficulty": row['demondifficulty'],
                            "maxgroups": row['maxgroups']
                        }
                    )

            elif isclaimsquery:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")
                
                    new_dict.append(
                        {
                            "collabid": row['collabid'],
                            "partid": row['partid'],
                            "userid": row['userid'], 
                            "status": row['status'],
                            "backups": row['backups']
                        }
                    )
            
            elif issongquery:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")
                
                    new_dict.append(
                        {
                            "songid": row['songid'],
                            "songname": row['songname'],
                            "artistid": row['artistid'], 
                            "artistname": row['artistname'],
                            "normalizedsongname": row['normalizedsongname'],
                            "normalizedartistname": row['normalizedartistname'],
                            "youtubeid": row['youtubeid'],
                            "newgroundsid": row['newgroundsid'],
                            "bandcampuser": row['bandcampuser'],
                            "bandcamptrack": row['bandcamptrack'],
                            "soundclouduser": row['soundclouduser'],
                            "soundcloudtrack": row['soundcloudtrack'],
                            "storagelocation": row['storagelocation'],
                            "youtubelink": row['youtubelink'],
                            "newgroundslink": row['newgroundslink'],
                            "bandcamplink": row['bandcamplink'],
                            "soundcloudlink": row['soundcloudlink'],
                            "replacementid": row['replacement_id'],
                            "isnong": row['isnong']
                            
                        }
                    )
            
            elif isartistquery:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")
                
                    new_dict.append(
                        {
                            "artistid": row['artistid'], 
                            "artistname": row['artistname'],
                            "normalizedname": row['normalizedname']                            
                        }
                    )
            
            elif isuserclaimsquery:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")
                
                    new_dict.append(
                        {
                            "claimid": row['claimid'],
                            "partid": row['partid'],
                            "collabid": row['collabid'],
                            "userid": row['userid'], 
                            "claimtype": row['claimtype'],
                            "claimstatus": row['claimstatus'],
                            "ratingatclaimtime": row['ratingatclaimtime']
                        }
                    )
            
            else:
                for row in insert:
                    if not isinstance(row, asyncpg.Record):
                        raise ValueError("List does not seem to contain Records")

                    if row['rating'] not in range(1,6):
                        raise TypeError("One of your ratings is not between 1 or 5 stars")

                    new_dict.append(
                        {
                            "partnumber": row['partid'],
                            "offsetstartseconds": float(row['offsetstart']), 
                            "offsetendseconds": float(row['offsetend']),
                            "offsetstarttime": None,
                            "offsetendtime": None,
                            "rating": row['rating']
                        }
                    )

        case _:
            raise TypeError("Not a list of Records or a DataFrame.")
    
    if not iscollabquery and not isclaimsquery and not issongquery and not isartistquery and not isuserclaimsquery:
        for part in new_dict:
            if part["offsetstartseconds"] > part["offsetendseconds"]:
                raise TypeError("One of your parts has a larger Offset Start than its Offset End.")

            part["offsetstarttime"] = await parse_seconds_to_time(
                part["offsetstartseconds"]
            )

            part["offsetendtime"] = await parse_seconds_to_time(
                    part["offsetendseconds"]
            )

    return new_dict