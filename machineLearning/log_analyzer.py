import csv
import matplotlib.pyplot as plt
import sys
import os

def analyze_application(file_path):
    record = []
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)
        total_psize = 0
        for row in spamreader:
            if int(row[1]) == 0: # not send record
                timestamp = int(row[0])/1e9
                total_psize += int(row[7])
                record.append([timestamp, total_psize])

    record.sort(key=lambda ele:ele[0])
    x, y = [], []
    for pair in record:
        x.append(pair[0])
        y.append(pair[1])
    sent_packet_size, = plt.plot(x, y, 'go')
    plt.legend([sent_packet_size], ['sent packet size'], loc='upper left')
    plt.title('Time-Sent packet size')
    plt.xlabel('Time / s', fontsize = 14, color = 'black')
    plt.ylabel('Sent packet size / Byte', fontsize = 14, color = 'black')
    print 'server send total: ', y[-1], ' Bytes' 

def analyze_client_end_node(file_path):
    record = []
    # '/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_client'
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)
        for row in spamreader:
            if int(row[1]) == 1: # not receive record
                timestamp = int(row[0])/1e9
                subflowId = int(row[3])
                seqnum = int(row[4])
                if subflowId >= 0: # for non-mptcp packet, subflowId will be -1
                    record.append([timestamp, subflowId, seqnum])

    record.sort(key=lambda ele:ele[0])
    x, y = [[],[]], [[],[]]
    for row in record:
        # subflow id is from 0 to n-1
        x[row[1]].append(row[0])
        y[row[1]].append(row[2])
    print len(y),len(y[0]),len(y[1])
    subflow_1, = plt.plot(x[0], y[0], 'ro')
    subflow_2, = plt.plot(x[1], y[1], 'bo')
    plt.legend([subflow_1, subflow_2], ['client side subflow 1', 'client side subflow 2'], loc='upper left')
    plt.title('Client Side Time-Seqence number, Max SeqSum == ' + str(sum([row[-1] for row in y])))
    plt.xlabel('Time / s', fontsize = 14, color = 'black')
    plt.ylabel('Seqence number', fontsize = 14, color = 'black')
    writeToCsv(sentBytes = sum([row[-1] for row in y]))

def analyze_server_end_point(file_path):
    record = []
    # '/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_client'
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)
        for row in spamreader:
            if int(row[1]) == 0: # not send record
                timestamp = int(row[0])/1e9
                subflowId = int(row[3])
                seqnum = int(row[4])
                if subflowId >= 0: # for non-mptcp packet, subflowId will be -1
                    record.append([timestamp, subflowId, seqnum])

    record.sort(key=lambda ele:ele[0])
    x, y = [[],[]], [[],[]]
    for row in record:
        # subflow id is from 0 to n-1
        x[row[1]].append(row[0])
        y[row[1]].append(row[2])
    subflow_1, = plt.plot(x[0], y[0], 'ro')
    subflow_2, = plt.plot(x[1], y[1], 'bo')
    plt.legend([subflow_1, subflow_2], ['server side subflow 1', 'server side subflow 2'], loc='upper left')
    plt.title('Server Side Time-Seqence number, Max SeqSum == ' + str(sum([row[-1] for row in y])))
    plt.xlabel('Time / s', fontsize = 14, color = 'black')
    plt.ylabel('Seqence number', fontsize = 14, color = 'black')
    writeToCsv(receivedBytes = sum([row[-1] for row in y]))

def analyze_flow(file_path):
    mptcp_subflow_id = [-1]*4
    record = []
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)
        for row in spamreader:
            timestamp = int(row[0])/1e9
            flowId = int(row[1])
            From = row[2]
            To = row[3]
            TxPacket = int(row[4])
            RxPacket = int(row[6])
            delaySum = float(row[8][1:-2])/1e9
            lostPackets = int(row[10])

            record.append([timestamp, flowId, TxPacket, RxPacket, delaySum, lostPackets])
            if -1 in mptcp_subflow_id:
                if flowId not in mptcp_subflow_id:
                    if From == '192.168.0.1' and To == '192.168.9.2':
                        mptcp_subflow_id[1] = flowId
                    elif From == '192.168.9.2' and To == '192.168.0.1':
                        mptcp_subflow_id[0] = flowId
                    elif From == '192.168.0.1' and To == '192.168.11.2':
                        mptcp_subflow_id[3] = flowId
                    elif From == '192.168.11.2' and To == '192.168.0.1':
                        mptcp_subflow_id[2] = flowId

    print 'mptcp subflow ids: ', mptcp_subflow_id
    record.sort(key=lambda ele:ele[0])
    
    x = [[],[],[],[]]
    y = [[],[],[],[]]
    for row in record:
        # flow id is from 1 to N,
        if row[1] in mptcp_subflow_id:
            x[mptcp_subflow_id.index(row[1])].append(row[0]) # append time stamp for flow with id row[1]
            y[mptcp_subflow_id.index(row[1])].append(row[2]) # append TxPacket num for flow with id row[1]

    s_c_subflow_1, = plt.plot(x[0], y[0], 'r-', linewidth=2.0) # s->c 1
    c_s_subflow_1, = plt.plot(x[1], y[1], 'r-.', linewidth=2.0) # c->s 1
    s_c_subflow_2, = plt.plot(x[2], y[2], 'b-', linewidth=2.0) # s->c 2
    c_s_subflow_2, = plt.plot(x[3], y[3], 'b-.', linewidth=2.0) # c->s 2
    plt.legend([s_c_subflow_1, c_s_subflow_1, s_c_subflow_2, c_s_subflow_2],
               ['server to client packet number over subflow 1', 'client to server packet number over subflow 1',
                'server to client packet number over subflow 2', 'client to server packet number over subflow 2'], loc='upper left')
    plt.title('Time-TxPacket')
    plt.xlabel('Time / s', fontsize = 14, color = 'black')
    plt.ylabel('Packet number', fontsize = 14, color = 'black')

def analyze_reward(file_path):
    record = []
    # '/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_client'
    with open(file_path, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        next(spamreader)
        for row in spamreader:
            timestamp = int(row[0])/1e9
            reward = int(row[1])
            record.append([timestamp, reward])

    record.sort(key=lambda ele:ele[0])
    x, y = [], []
    for pair in record:
        x.append(pair[0])
        y.append(pair[1])
    reward_plt, = plt.plot(x, y, 'k-')
    plt.legend([reward_plt], ['reward'], loc='best')
    plt.title('Time-Reward')
    plt.xlabel('Time / s', fontsize = 14, color = 'black')
    plt.ylabel('Reward', fontsize = 14, color = 'black')

def writeToCsv(sentBytes = None, receivedBytes = None):
    if(len(sys.argv) >= 4 and sys.argv[2] == 'true'):
        path = sys.argv[3]
        scheduler = sys.argv[4]

        assert os.path.isfile(path) 
        new_rows = []
        with open(path, 'rb') as csv_file:
            r = csv.reader(csv_file)
            row_num = 0
            for row in r:
                if row_num == 0 and scheduler == 'rr' and sentBytes is not None:
                    row.append(sentBytes)
                elif row_num == 1 and scheduler == 'rtt' and sentBytes is not None:
                    row.append(sentBytes)
                elif row_num == 2 and scheduler == 'rf' and sentBytes is not None:
                    row.append(sentBytes)
                elif row_num == 3 and scheduler == 'ldbp' and sentBytes is not None:
                    row.append(sentBytes)
                elif row_num == 4 and scheduler == 'rr' and receivedBytes is not None:
                    row.append(receivedBytes)
                elif row_num == 5 and scheduler == 'rtt' and receivedBytes is not None:
                    row.append(receivedBytes)
                elif row_num == 6 and scheduler == 'rf' and receivedBytes is not None:
                    row.append(receivedBytes)
                elif row_num == 7 and scheduler == 'ldbp' and receivedBytes is not None:
                    row.append(receivedBytes)
                row_num += 1
                new_rows.append(row)

        with open(path, 'wb') as csv_file:
            w = csv.writer(csv_file)
            w.writerows(new_rows)
                
if __name__ == '__main__':
    # plt.subplot(4,1,1)
    # analyze_application('/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_server')
    # plt.subplot(4,1,2)
    # analyze_client_end_node('/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_client')
    # plt.subplot(4,1,3)
    # analyze_server_end_point('/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_server')
    # plt.subplot(4,1,4)
    # analyze_flow('/home/hong/workspace/mptcp/ns3/mptcp_output/mptcp_server_cWnd')
    # plt.show()

    # batch_num = int(sys.argv[1])
    # plt.subplot(4,1,1)
    # analyze_application('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_mptcp_client')
    # # analyze_application('/home/hong/workspace/mptcp/ns3/rl_training_data_wrong/' + str(batch_num) + '_mptcp_server')
    # # analyze_flow('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_mptcp_server_cWnd')
    # # analyze_reward('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_calculate_reward')
    # plt.subplot(4,1,2)
    # analyze_client_end_node('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_mptcp_client')
    # plt.subplot(4,1,3)
    # analyze_server_end_point('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_mptcp_server')
    # plt.subplot(4,1,4)
    # analyze_flow('/home/hong/workspace/mptcp/ns3/rl_training_data/' + str(batch_num) + '_mptcp_server_cWnd')
    # plt.show()
    print sys.argv[1] ,sys.argv[2], sys.argv[3], sys.argv[4]

    writeToCsv(12,223)
