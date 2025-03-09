import logging

from lib.fc.modload.modload import loader

 
log = logging.getLogger('fc.net.sys')


async def status_page(req,resp):
    with loader('fc.app.system_route_impl') as impl:
        return await impl.status_page(req,resp)
        
async def config_page(req,resp,message = "Configuration"):
    with loader('fc.app.system_route_impl') as impl:
        return await impl.config_page(req,resp)
    
async def update_config(req,resp):
    with loader('fc.app.system_route_impl') as impl:
        return await impl.update_config(req,resp)
        
async def reboot(req,resp):
    with loader('fc.app.system_route_impl') as impl:
        return await impl.reboot(req,resp)


async def create_routes():
    with loader('fc.net.http.route') as routes:
        GET = routes.GET
        POST = routes.POST
        router = routes.create_router('System')
        routes.add_route(router,GET,"/status",status_page)
        routes.add_route(router,GET,"/config",config_page)   
        routes.add_route(router,POST,"/config",update_config)
        routes.add_route(router,POST,"/reboot", reboot)
        return router 
    