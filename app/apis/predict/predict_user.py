from pydantic import BaseModel
from random import randint

class User(BaseModel):
    user: str
    password: str
    folder: str
    url: str

#TODO: cambiar a una base de datos o archivo de configuracion
USERS = [User(user='erick.moreno@troiatec.com'
                    , password='Troiatec2023$'
                    , folder='/predict/folder/a6c2b8b8-cded-49a4-b7a2-fd2808f443e5'
                    , url='https://app.neuronsinc.com/predict/folder/a6c2b8b8-cded-49a4-b7a2-fd2808f443e5')

        , User(user='juan.roberto@troiatec.com'
                    , password='Troiatec060112#'
                    # https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e?predictionType=formatted
                    , folder='/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e'
                    , url='https://app.neuronsinc.com/predict/folder/6ad1e02a-9281-44e6-b20f-2e167453da0e')

        , User(user='kevyn.lopez@troiatec.com'
                    , password='Troiatec2023$'
                    , folder='/predict/folder/b49f8374-4bdf-4511-a6c1-d95e63de0504'
                    , url='https://app.neuronsinc.com/predict/folder/b49f8374-4bdf-4511-a6c1-d95e63de0504')

        , User(user='o.rivera@troiatec.com'
                    , password='Troiatec2023$'
                    , folder='/predict/folder/0e3ed6c1-9976-4502-b693-1b3b3b4b63bd'
                    , url='https://app.neuronsinc.com/predict/folder/0e3ed6c1-9976-4502-b693-1b3b3b4b63bd')

        , User(user='c.castillo@troiatec.com'
                    , password='Troiatec2023$'
                    , folder='/predict/folder/d6148517-eb51-4e68-a8d9-0c6b101e8097'
                    , url='https://app.neuronsinc.com/predict/folder/d6148517-eb51-4e68-a8d9-0c6b101e8097')]



class UserList:
    def get_user(self, position: int = -1) -> User:
        if(position == -1):
            position = randint(0,4)

        return USERS[position]

    def get_all_users(self) -> User:
        return iter(USERS)

    def get_length(self) -> int:
        return len(USERS)
