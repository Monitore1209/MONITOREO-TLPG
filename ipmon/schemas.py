'''Esquemas utilizados para APIs'''
from marshmallow import Schema

class UsersSchema(Schema):
    '''Esquema de usuarios'''
    class Meta:
        '''Metadata'''
        fields = ('id', 'username', 'password', 'email', 'date_created', 'alerts_enabled')


class HostsSchema(Schema):
    '''Esquema de Hosts'''
    class Meta:
        '''Meta'''
        fields = ('id', 'ip_address', 'hostname', 'ciudad' , 'cto', 'dispositivo', 'tipo', 'status', 'last_poll', 'status_change_alert', 'previous_status', 'alerts_enabled')


class PollHistorySchema(Schema):
    '''Esquema del historial de sondeos'''
    class Meta:
        '''Meta'''
        fields = ('id', 'host_id', 'poll_time', 'poll_status', 'date_created')


class HostAlertsSchema(Schema):
    '''Esquema de alertas del host'''
    class Meta:
        '''Meta'''
        fields = ('id', 'hostname', 'ip_address', 'host_status', 'poll_time', 'alert_cleared', 'date_created', 'host_id')


class PollingConfigSchema(Schema):
    '''Esquema de sondeo'''
    class Meta:
        '''Meta'''
        fields = ('id', 'poll_interval', 'history_truncate_days')


class SmtpConfigSchema(Schema):
    '''Esquema SMTP'''
    class Meta:
        '''Meta'''
        fields = ('id', 'smtp_server', 'smtp_port', 'smtp_sender','smtp_user','smtp_password'  )


class WebThemesSchema(Schema):
    '''Esquema Temas Web '''
    class Meta:
        '''Meta'''
        fields = ('id', 'theme_name', 'theme_path', 'active')


class Schemas():
    '''Métodos estáticos para acceder a esquemas'''

    @staticmethod
    def users(many=True):
        """user(s)

        Args:
            many (bool, optional): Return multiple results. Defaults to True.

        Returns:
            UsersSchema: Schema object
        """        
        return UsersSchema(many=many)


    @staticmethod
    def hosts(many=True):
        """host(s)

        Args:
            many (bool, optional): Return multiple results. Defaults to True.

        Returns:
            HostsSchema: Schema object
        """      
        return HostsSchema(many=many)


    @staticmethod
    def poll_history(many=True):
        """poll history

        Args:
            many (bool, optional): Return multiple results. Defaults to True.

        Returns:
            PollHistorySchema: Schema object
        """      
        return PollHistorySchema(many=many)


    @staticmethod
    def host_alerts(many=True):
        """host alerts

        Args:
            many (bool, optional): Return multiple results. Defaults to True.

        Returns:
            HostAlertsSchema: Schema object
        """      
        return HostAlertsSchema(many=many)


    @staticmethod
    def polling_config():
        """smtp config

        Returns:
            PollingConfigSchema: Schema object
        """ 
        return PollingConfigSchema()


    @staticmethod
    def smtp_config():
        """smtp config

        Returns:
            SmtpConfigSchema: Schema object
        """        
        return SmtpConfigSchema()


    @staticmethod
    def web_themes(many=True):
        """web themes

        Args:
            many (bool, optional): Return multiple results. Defaults to True.

        Returns:
            WebThemesSchema: Schema object
        """      
        return WebThemesSchema(many=many)

