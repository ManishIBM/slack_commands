import json
import os
from datetime import timedelta, datetime


class ClusterDbMgmt:
    def __init__(self, db_path='cluster_info.json'):
        print("in Cluster db management")
        self.__db_path = db_path
        self._db_data = self.get_db_data()
        if not self._db_data:
            self._db_data = {}

    def get_db_data(self):
        try:
            with open(self.__db_path) as fp:
                self._db_data = json.load(fp)
                return self._db_data
        except (FileNotFoundError, Exception) as e:
            print('Exception found: {}'.format(str(e)))

    def is_cluster_exist(self, user_name, cluster_info):
        if user_name not in self._db_data:
            return False
        for cluster in self._db_data[user_name]:
            if cluster.get('name') == cluster_info.get('name'):
                return True
        return False

    def update_cluster_attribute(self, user_name, attribute_info):
        print("in update cluster attribute")
        cluster_exist = False
        if not (self._db_data and user_name in self._db_data.keys()):
            return "username doesn't exist"
        for cluster in self._db_data[user_name]:
            if cluster.get('name') == attribute_info.get('name'):
                cluster_exist = True
                cluster.update(attribute_info)
        if not cluster_exist:
            return "cluster doesn't exist"
        self.update_db()
        return "success"

    def get_expiring_clusters(self, exp_interval):
        """
        The function checks the expiration time with respect to current time
        if the difference is less than exp_interval, a dictionary will be
        returned with cluster name and remaining hours
        :param exp_interval: interval to check the expiration
        :type exp_interval:
        :return: dictionary of cluster name and remaining hours
        :rtype: dict
        """
        print('in get expiring cluster')
        cluster_time_dic = {}
        for user, clusters in self._db_data.items():
            for cluster in clusters:
                exp_time = datetime.strptime(cluster['expiration_time'], '%Y-%m-%d %H:%M:%S')
                diff = int((exp_time - datetime.now()).total_seconds()/3600)
                if diff <= exp_interval:
                    cluster_time_dic[cluster.get('name')] = str(diff)+" hrs"
        return cluster_time_dic

    def update_cluster_info(self, user_name, cluster_info):
        try:
            updated_data = {}
            self.get_db_data()
            if self._db_data and user_name in self._db_data.keys():
                if self.is_cluster_exist(user_name, cluster_info):
                    return 'cluster already exist'
                self._db_data[user_name].append(cluster_info)
            else:
                self._db_data[user_name] = [cluster_info]
            if self._db_data:
                print("updated data: {}".format(self._db_data))
            self.update_db()
            return 'success'
        except (FileNotFoundError, Exception) as e:
            print('Exception found: {}'.format(str(e)))
            return 'failed'

    def delete_record(self, user_id, cluster_name):
        index = 0
        is_present = False
        for item in self._db_data.get(user_id):
            if item.get('name') == cluster_name:
                is_present = True
                break
            index += 1
        if is_present:
            self._db_data.get(user_id).pop(index)
            self.update_db()
            return "cluster deletion initiated"
        else:
            return "cluster name/user id not found"

    def update_db(self):
        try:
            with open(self.__db_path, 'w') as fp:
                json.dump(self._db_data, fp, indent=4)
        except (FileNotFoundError, Exception) as e:
            print('Exception found: {}'.format(str(e)))
            return 'failed'

    def get_clusters_by_user(self, user_name, refresh_data=False):

        if refresh_data:
            self.get_db_data()

        return self._db_data[user_name]

    def delete_cluster(self, user_name, cluster_info):
        return "in delete cluster for user {} and clsuter".format(user_name,
                                                                  cluster_info)


class ClusterMgmt(ClusterDbMgmt):
    def __init__(self):
        super().__init__()
        self.config_data = None
        print("in Cluster management class")

    def set_config_data(self, config_data):
        self.config_data = config_data

    def initiate_cluster_creation(self, user_name, cmd_text):
        print("Initiating cluster creation using Jenkin's Job")
        try:
            cmd_text = cmd_text.split(',')
            error_msg = ''
            cluster_dict = {}
            for param in cmd_text:
                param = param.strip()
                if not param:
                    continue
                cmd_value = param.split(':')
                key = cmd_value[0].strip()
                value = cmd_value[1].strip()
                cluster_dict[key] = value

                if key == 'type' and value not in self.config_data[
                    'CLOUD_TYPE']:
                    error_msg += "wrong cloud type {}. Provide any value among {} \n".format(
                        value, self.config_data['CLOUD_TYPE'])
                    return error_msg

            if self.is_cluster_exist(user_name, cluster_dict):
                return 'cluster already exist, plz try with another name'

            data = {"AWS_CLUSTER_NAME": cluster_dict['name'],
                    "CLUSTER_OWNER": user_name}
            if cluster_dict.get('type'):
                data['AWS_TYPE'] = cluster_dict.get('type')
            if cluster_dict.get('region'):
                data['AWS_REGION'] = cluster_dict.get('region')
            if cluster_dict.get('version'):
                data['OCP_VERSION'] = cluster_dict.get('version')
            if cluster_dict.get('node_type'):
                data['COMPUTE_NODE_TYPE'] = cluster_dict.get('node_type')
            if cluster_dict.get('node_num'):
                data['COMPUTE_NODE_NUMBER'] = cluster_dict.get('node_num')

            ret = self.initiate_jenkins_build(
                url=self.config_data['JENKINS_AWS_CREATE'], data=data)
            print(ret)
            if ret.status_code != 201:
                return "Jenkins pipeline build failed to initiate and returned: {}".format(
                    ret.status_code)

            cluster_dict['status'] = "creating"
            current_datetime = datetime.now()
            cluster_dict['creation_time'] = current_datetime.strftime(
                "%Y-%m-%d %H:%M:%S")
            duration = self.config_data.get('CLUSTER_EXPIRATION_DURATION')*24
            expiration = current_datetime + timedelta(
                hours=duration)
            cluster_dict['expiration_time'] = expiration.strftime(
                "%Y-%m-%d %H:%M:%S")
            if error_msg != "":
                return error_msg
            ret = self.update_cluster_info(user_name, cluster_dict)
            if ret != 'success':
                return ret
            # return "cluster creation initiated"

            print(ret)
            return "cluster creation initiated"
        except Exception as e:
            print('Exception found: {}'.format(str(e)))
            return "exception occurred"

    def delete_cluster(self, user_id, cmd_text):
        print("In delete cluster")
        cluster_name = cmd_text.strip()
        url = self.config_data['JENKINS_AWS_DELETE']
        ret = self.initiate_jenkins_build(url, {'AWS_CLUSTER_NAME': cluster_name})
        if ret.status_code != 201:
            return "Jenkins pipeline build failed to initiate and returned: {}".format(
                ret.status_code)
        return "cluster deletion initiated"

    def initiate_jenkins_build(self, url, data):
        import requests
        print('rest call of url {} with data {}'.format(url, data))
        ret = requests.post(
            url=url,
            auth=(os.environ['JENKINS_USER'], os.environ['JENKINS_PWD']),
            data=data)

        return ret
