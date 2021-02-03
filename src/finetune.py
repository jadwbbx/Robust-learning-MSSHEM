from train import *
from utils import *
from attack_adv import *
import os, argparse


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default='')
    parser.add_argument("--which_data", type=str, default='排比')
    parser.add_argument("--device", type=str, default='cuda:0')
    parser.add_argument("--max_iters", type=int, default=20)
    parser.add_argument('--pretrained_model_path', type=str, default='/share/Guowei/acl_robust_nlp/chinese_wwm_pytorch')
    parser.add_argument('--num_classes', type=int, default=2)
    parser.add_argument("--synonyms_path", type=str, default='/share/Guowei/acl_robust_nlp/形近字.json')
    parser.add_argument("--vocab_path", type=str, default='/share/Guowei/acl_robust_nlp/3500常用汉字.txt')
    parser.add_argument("--augmentation", type=str, default='')


    args = parser.parse_args()
    checkpoint = args.checkpoint
    which_data = args.which_data
    device = args.device
    max_iters = args.max_iters
    pretrained_model_path = args.pretrained_model_path
    num_classes = args.num_classes
    synonyms_path = args.synonyms_path
    vocab_path = args.vocab_path
    augmentation = args.augmentation

    train_data = load_json('/share/Guowei/acl_robust_nlp/data/text_classification/{}/train.json'.format(which_data))['data']

    if(augmentation=='clean_data'):
        pass
    elif(augmentation=='rule_data'):
        train_data += load_json('/share/Guowei/acl_robust_nlp/model_and_data/规则造错/{}/data/train.json'.format(which_data))['data']
    elif(augmentation=='model_data'):
        train_data += load_json('/share/Guowei/acl_robust_nlp/model_and_data/模型造错/{}/data/train.json'.format(which_data))['data']
    elif(augmentation=='attack_data'):
        synonyms = load_json(synonyms_path)
        vocab_lst = load_txt(vocab_path)

        print('attacking training data, please wait...')
        attacked_data_save_path = '/share/Guowei/acl_robust_nlp/model_and_data/对抗样本/{}/data'.format(which_data)
        os.makedirs(attacked_data_save_path, exist_ok=True)

        attacked_data = create_adv_data(checkpoint, gsgr, train_data, synonyms, vocab_lst, device, bs=20)
        save_json(attacked_data, os.path.join(attacked_data_save_path, 'train.json'))
        print('finish attacks..')
        train_data += attacked_data

    elif(augmentation=='all_data'):
        synonyms = load_json(synonyms_path)
        vocab_lst = load_txt(vocab_path)

        print('attacking training data, please wait...')
        attacked_data_save_path = '/share/Guowei/acl_robust_nlp/model_and_data/对抗样本/{}/data'.format(which_data)
        os.makedirs(attacked_data_save_path, exist_ok=True)

        attacked_data = create_adv_data(checkpoint, gsgr, train_data, synonyms, vocab_lst, device, bs=20)
        save_json(attacked_data, os.path.join(attacked_data_save_path, 'train.json'))
        print('finish attacks..')
        train_data += attacked_data
        
        print('loading ruled and modeled data')
        train_data += load_json('/share/Guowei/acl_robust_nlp/model_and_data/规则造错/{}/data/train.json'.format(which_data))['data']
        train_data += load_json('/share/Guowei/acl_robust_nlp/model_and_data/模型造错/{}/data/train.json'.format(which_data))['data']


    valid_data = load_json('/share/Guowei/acl_robust_nlp/data/text_classification/{}/valid.json'.format(which_data))['data']
    
    print('train size {}, valid size {}'.format(len(train_data), len(valid_data)), flush=True)

    learning_rate_lst = [5e-8]
    batch_size_lst = [10]
    loss_fn = F.cross_entropy
    best_model_save_path = '/share/Guowei/acl_robust_nlp/model/{}/{}'.format(which_data, augmentation)

    for learning_rate in learning_rate_lst:
        for batch_size in batch_size_lst:

            model_prefix = '{}_finetune'.format(checkpoint.split('/')[-1].replace('.pt', ''))
            
            print('start finetuning model {}, with lr {}, batch_size {}'.format(model_prefix, learning_rate, batch_size))
            model = load_model(checkpoint, device, pretrained_model_path=pretrained_model_path)
            train_helper(model, learning_rate, loss_fn, train_data, valid_data, batch_size, device, \
                max_iters, best_model_save_path, model_prefix, save_every_epoch=True)