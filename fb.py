import fitbit

class Fb:
    def __init__(self, config):
        self.config = config
        self.consumer_key = self.config.get('Fitbit', 'consumer_key')
        self.consumer_secret = self.config.get('Fitbit', 'consumer_secret')
        self.oauth_token = self.config.get('Fitbit', 'token')
        self.oauth_token_secret = self.config.get('Fitbit', 'secret')
        self.bf_goal = 15.0
        self.bf_start = 21.3
        self.bw_goal = 175.0
        self.bw_start = 182.1
    
    def connect_to_fitbit(self):
        self.authd_client = fitbit.Fitbit(self.consumer_key, self.consumer_secret, resource_owner_key=self.oauth_token, resource_owner_secret=self.oauth_token_secret)
        self.authd_client.sleep()

    def get_data(self):
        #self.bf_goal = self.authd_client.body_fat_goal()['goal']['fat']
        #self.bw_goal = self.authd_client.body_weight_goal()['goal']['weight']
        #self.bw_start = self.authd_client.body_weight_goal()['goal']['startWeight']
        self.bf = float(self.authd_client.get_bodyfat(period='7d')['fat'][-1]['fat'])
        self.bw = float(self.authd_client.get_bodyweight(period='7d')['weight'][-1]['weight'])
        self.bf_month = self.authd_client.get_bodyfat(period='1m')
        self.bw_month = self.authd_client.get_bodyweight(period='1m')

    def get_html(self):
        html = ''
        html = html + 'Body Fat Goal: %2.2f <br />' % (self.bf_goal)
        html = html + 'Body Fat: %2.2f <br />' % (self.bf)
        html = html + 'Body Fat Goal Percent: %2.2f <br />' % ((self.bf_start - self.bf) / (self.bf_start - self.bf_goal) * 100)
        html = html + 'Body Weight Goal: %3.2f <br />' % (self.bw_goal)
        html = html + 'Body Weight: %3.2f <br />' % (self.bw)
        html = html + 'Body Weight Goal Percent: %2.2f <br />' % ((self.bw_start - self.bw) / (self.bw_start - self.bw_goal) * 100)
        return html
