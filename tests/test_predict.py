from app.apis.predict import predict, driver
from app.apis.predict.predict_user import User, UserList

from app.apis.predict.download_watcher import downloaded_file

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium import webdriver

import pytest


def test_predict_bot_correct_login() -> None:
    user:User = UserList().get_user()
    d = driver.configure_driver()
    sipudo = predict.login(user=user, driver=d)

    assert(sipudo.current_url == f"{user.url}?predictionType=formatted")
    assert(type(sipudo) == WebDriver)
    d.quit()

# def test_predict_all_correct_login() -> None:
#     for u in UserList().get_all_users():
#         print(u)
#         user:User = u
#         d = driver.configure_driver()
#         sipudo = predict.login(user=user, driver=d)

#         assert(d.current_url == f"{user.url}?predictionType=formatted")
#         assert(True == sipudo)
#         d.quit()


def test_predict_bot_with_wrong_login() -> None:
    user:User = UserList().get_user()
    user.password = user.password + "1"
    d = driver.configure_driver()
    sipudo = predict.login(user=user, driver=d)

    assert(d.current_url != f"{user.url}?predictionType=formatted")
    assert(type(sipudo) == driver)
    d.quit()



def test_predic_bot_can_download_file() -> None:
    user:User = UserList().get_user(3)
    d = driver.configure_driver()
    sipudo = predict.download_file(user=user, driver=d, stimulus='password')
    assert(type(sipudo) == WebDriver)
    d.quit()

# def test_predic_bot_cant_download_file() -> None:
#     user:User = UserList().get_user(3)
#     d = driver.configure_driver()
#     with pytest.raises(Exception) as ex_info:
#         sipudo = predict.download_file(user=user, driver=d, stimulus='passwordss')
#         assert(type(sipudo) != WebDriver)
#         d.quit()

# def test_watchdog() -> None:
#     waiter = downloaded_file('archivito.zip')
#     waiter.start()


    

# def test_predic_bot_can_find_stimulu() -> None:
#     user:User = UserList().get_user(3)
#     d = driver.configure_driver()
#     result = predict.find_stimulu(user=user, driver=d, stimulus='password')
#     assert(type(result) == WebElement)
#     d.quit()


# def test_predic_bot_cannot_find_stimulu() -> None:
#     user:User = UserList().get_user(3)
#     d = driver.configure_driver()
#     with pytest.raises(Exception) as ex_info:
#         result = predict.find_stimulu(user=user, driver=d, stimulus='xxx')
#         print(ex_info)
#         assert(True)

#     d.quit()
