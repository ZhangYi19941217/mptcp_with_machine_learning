import socket
import pandas
import matplotlib.pyplot as plt
from time import sleep
from rl_socket import Interacter_socket
from RL_core import DeepQNetwork
from RL_core import extract_observation
from RL_core import calculate_reward
from RL_core import apply_action
from shutil import copyfile

'''
This file implements Deep Q-learning Network (DQN)
'''

def IsInt(s):
    # A naive method, but enough here
    if "." in s:
        return False
    else:
        return True

class DataRecorder():

    def __init__(self):
        self.next_seq_num = 0
        self.data = {}
        self.action = []

    def add_one_record(self, str_data):
        # name#value$name$value...
        pair_list = str_data.split("$")
        one_row = {}
        for pair in pair_list:
            if len(pair) > 3: # this ensures the string (pair) is not empty or string with single '$'
                name_val_list = pair.split("#")
                # print "Hong Jiaming: 1 ", pair, len(name_val_list), name_val_list[0], name_val_list[1]
                if IsInt(name_val_list[1]):
                    one_row[name_val_list[0]] = int(name_val_list[1])
                else:
                    one_row[name_val_list[0]] = float(name_val_list[1])

        # ensure this transmission is right and complete
        # neighbour TCP segments must not combined into one
        assert one_row["size"] == len(one_row)
        assert one_row["ssn"] == self.next_seq_num
        self.data[self.next_seq_num] = one_row
        self.next_seq_num += 1

    def get_data_dic(self):
        return self.data

    def get_latest_data(self):
        return self.data[self.next_seq_num-1]

    def add_pair_to_last_record(self, name, value):
        self.data[self.next_seq_num-1][name] = value

    def print_all_data(self):
        print "dic size: ", len(self.data)
        for ssn, data in self.data.iteritems():
            for k, v in data.iteritems():
                print "key: ", k, "value: ", v

    def print_latest_data(self):
        latest_data = self.data[self.next_seq_num-1]
        for k, v in latest_data.iteritems():
            print "key: ", k, "value: ", v

if __name__ == "__main__":
    episode_count = 0
    RL = DeepQNetwork(n_actions=4, n_features=4, learning_rate=0.01, reward_decay=0.9,
                      e_greedy=0.9, replace_target_iter=200, memory_size=2000, output_graph=True)
    reward_record = []
    while episode_count < 1:
        dataRecorder = DataRecorder()

        socket = Interacter_socket(host = '', port = 12345)
        socket.listen()
        recv_str, this_episode_done = socket.recv()

        if this_episode_done:
            print "RL server ended too early! " + recv_str; exit()

        dataRecorder.add_one_record(recv_str)
        observation_before_action = extract_observation(dataRecorder)
        reward = calculate_reward(dataRecorder, reset = True)

        print 'episode: ', episode_count
        f = open("/home/hong/workspace/mptcp/ns3/mptcp_output/calculate_reward", 'w'); f.write("time,reward\n")
        step = 0

        while True:
            # Choose action
            # print 'recv_str: ', recv_str
            # print 'observation: ', observation_before_action
            action = RL.choose_action(observation_before_action)

            # Apply action to environment
            apply_action(socket, dataRecorder, action)

            # Get feedback (observation, reward)
            recv_str, this_episode_done = socket.recv() # get new observation and reward

            if this_episode_done is True:
                break 

            dataRecorder.add_one_record(recv_str)
            observation_after_action = extract_observation(dataRecorder)
            reward = calculate_reward(dataRecorder)
            reward_record.append(reward)
            # # Update memory
            RL.store_transition(observation_before_action, action, reward, observation_after_action)

            if (step > 200) and (step % 5 == 0):
                RL.learn()

            observation_before_action = observation_after_action

            f.write(str(dataRecorder.get_latest_data()["time"]) + ',' + str(reward) + '\n')
            step += 1

        socket.close()
        socket = None
        f.close()

        copyfile("/home/hong/workspace/mptcp/ns3/mptcp_output/calculate_reward", '/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(episode_count) + '_calculate_reward')
        copyfile("/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_client", '/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(episode_count) + '_mptcp_client')
        copyfile("/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_drops", '/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(episode_count) + '_mptcp_drops')
        copyfile("/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_server", '/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(episode_count) + '_mptcp_server')
        copyfile("/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_server_cWnd", '/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(episode_count) + '_mptcp_server_cWnd')
        # # print "sleep 30 seconds from now"
        # # sleep(30)
        episode_count += 1
    RL.plot_cost()
    # plt.figure()
    # plt.plot(dataRecorder.action, 'or')
    # plt.show()
    plt.figure()
    plt.plot(reward_record, 'ro')
    plt.show()