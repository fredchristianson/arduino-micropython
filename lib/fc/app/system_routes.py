import logging

from lib.fc.modload.modload import loader

 
log = logging.getLogger('fc.app.http.sys')


def status_page(req):
    with loader('fc.app.system_route_handlers') as impl:
        return  impl.status_page(req)
        
def config_page(req):
    with loader('fc.app.system_route_handlers') as impl:
        return  impl.config_page(req)
    
def update_config(req):
    with loader('fc.app.system_route_handlers') as impl:
        return  impl.update_config(req)
        
def reboot(req):
    with loader('fc.app.system_route_handlers') as impl:
        return  impl.reboot(req)


async def create_routes():
    with loader('fc.net.http.router') as routes:
        GET = routes.GET
        POST = routes.POST
        router = routes.create_router('System')
        routes.add_route(router,GET,"/status",status_page)
        routes.add_route(router,GET,"/config",config_page)   
        routes.add_route(router,POST,"/config",update_config)
        routes.add_route(router,POST,"/reboot", reboot)
        return router 
    