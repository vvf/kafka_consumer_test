import pytest
from asynctest import MagicMock
from sqlalchemy.orm import selectinload

from models.order import Order
from sqlalchemy import select

import dispatcher

@pytest.fixture
def message():
    msg = MagicMock()
    msg.value = '''
<ORDERS>
    <ORDER>
        <STATUS>STARTED</STATUS>
        <COMMENT>Тестовый заказ</COMMENT>
        <SOURCE>Новосибирск</SOURCE>
        <DESTINATION>Москва</DESTINATION>
        <SENDINGS>
            <SENDING>
                <DESTINATION>Новосибирск сортировочная</DESTINATION>            
            </SENDING>        
            <SENDING>
                <DESTINATION>Москва</DESTINATION>            
            </SENDING>        
        </SENDINGS>        
    </ORDER>
    <ORDER>
        <STATUS>IN_PROGRESS</STATUS>
        <COMMENT>Тестовый заказ #2</COMMENT>
        <SOURCE>Тамбов</SOURCE>
        <DESTINATION>Москва</DESTINATION>
        <SENDINGS>
            <SENDING>
                <DESTINATION>Новосибирск сортировочная</DESTINATION>            
            </SENDING>        
            <SENDING>
                <DESTINATION>Москва</DESTINATION>            
            </SENDING>        
        </SENDINGS>        
    </ORDER>
</ORDERS>
'''
    return msg

@pytest.mark.asyncio
async def test_dispatch(db, message):
    await dispatcher.dispatch(message)
    orders = await db.execute(select(Order).options(selectinload(Order.sendings)))
    for (order,) in orders:
        assert order.id is not None
        assert order.dest_station == "Москва"
        assert order.status is not None
        assert order.comment is not None
        assert len(order.sendings) == 2
        assert [s.dest_station for s in order.sendings] == ["Новосибирск сортировочная", "Москва"]
        await db.delete(order)