import time
import uuid
import yaml
import boto3
import telebot
import secrets
import requests


class LobbyNotFound(Exception):
    pass


class LobbyUserExists(Exception):
    pass


class LobbyMaxUsers(Exception):
    pass


class LobbyPermissions(Exception):
    pass


class Lobby:
    def __init__(self, config, lobbyId=None):
        self.c = config
        self.telegram = telebot.TeleBot(self.c['T_TOKEN'])
        self.db = boto3.resource('dynamodb').Table(self.c['TABLE'])
        if lobbyId:
            self._load(lobbyId)


    def _load(self, lobbyId):
        l = self.db.get_item(Key={'lobbyId': lobbyId})
        if 'Item' in l:
            for attr in l['Item']:
                setattr(self, attr, l['Item'][attr])
        else:
            raise LobbyNotFound()


    def _save(self):
        l = {}
        for attr in self.__dict__:
            val = getattr(self, attr)
            if type(val) in [int, str, dict, list, bool]:
                l[attr] = val
        self.db.put_item(Item=l)


    def _create_slots(self):
        for user in self.c['USERS']:
            if user not in self.joined:
                self.slots[str(uuid.uuid4())[:8]] = user


    def _notify_slots(self):
        for slot in self.slots:
            user = self.slots[slot]
            inviteUrl = self.c['API'] + self.lobbyId + '/' + slot + '/join'
            chatId = self.c['USERS'][user]['telegram']
            msg = f"[Join {self.name}!]({inviteUrl})"
            self.telegram.send_message(text=msg, chat_id=chatId, parse_mode='Markdown')


    def _notify_create(self):
        joined = [j[:-5] for j in self.joined]
        msg = f'{", ".join(joined)} created {self.name}'
        for chan in self.c['T_CHANNELS']:
            self.telegram.send_message(text=msg, chat_id=chan, parse_mode='Markdown')


    def _notify_join(self, user):
        for hook in self.c['D_WEBHOOKS']:
            r = requests.post(hook, json={'username': self.name, 'content': f'{user[:-5]} joined'})
        for chan in self.c['T_CHANNELS']:
            self.telegram.send_message(text=f'{user[:-5]} joined `{self.name}`', chat_id=chan, parse_mode='Markdown')


    def new(self, creator, max=5, public=False, joined=[], expireMins=60):
        if creator not in joined:
            joined.append(creator)
        setattr(self, 'creator', creator)
        setattr(self, 'lobbyId', str(uuid.uuid4())[:8])
        setattr(self, 'name', rand_lobby_name())
        setattr(self, 'max', max)
        setattr(self, 'creator', creator)
        setattr(self, 'joined', joined)
        setattr(self, 'expires', int(time.time()) + (60*expireMins))
        setattr(self, 'public', public)
        setattr(self, 'slots', {}) # self.loadSLots?
        self._create_slots()
        self._save()
        self._notify_create()
        self._notify_slots()
        return self


    def join(self, user):
        if not self.public and user not in self.c['USERS']:
            raise LobbyPermissions()
        elif user in self.joined:
            raise LobbyUserExists()
        elif self.max <= len(self.joined):
            raise LobbyMaxUsers()
        else:
            self.joined.append(user)
            self._save()
            self._notify_join(user)
            return self


def load_config():
    with open('config.yml', 'r') as cfg:
        try:
            return yaml.safe_load(cfg)
        except yaml.YAMLError as exc:
            print(exc)


def rand_lobby_name(prefix='', suffix='-mutants'):
    adjectives = [
        'lean',
        'ethereal',
        'impolite',
        'chilly',
        'supreme',
        'materialistic',
        'daffy',
        'measly',
        'previous',
        'apathetic',
        'terrible',
        'telling',
        'screeching',
        'ill',
        'frequent',
        'true',
        'fallacious',
        'wild',
        'rare',
        'infamous',
        'tidy',
        'tasty',
        'cooing',
        'entertaining',
        'vulgar',
        'milky',
        'huge',
        'unnatural',
        'woebegone',
        'marvelous',
        'kaput',
        'spotless',
        'peaceful',
        'fumbling',
        'dangerous',
        'big',
        'waiting',
        'dead',
        'bawdy',
        'polite',
        'squeamish',
        'empty',
        'easy',
        'drunk',
        'closed',
        'damp',
        'wiry',
        'cloudy',
        'plastic',
        'valuable',
        'aggressive',
        'rotten',
        'hesitant',
        'hollow',
        'powerful',
        'truthful',
        'historical',
        'addicted',
        'super',
        'thinkable',
        'debonair',
        'lowly',
        'marked',
        'outrageous',
        'lazy',
        'quiet',
        'insidious',
        'wealthy',
        'mushy',
        'forgetful',
        'wry',
        'next',
        'jazzy',
        'raspy',
        'meek',
        'tangible',
        'motionless',
        'disgusting',
        'bloody',
        'scintillating',
        'nutritious',
        'lackadaisical',
        'elastic',
        'rigid',
        'well',
        'tremendous',
        'abrasive',
        'magnificent',
        'striped',
        'false',
        'colorful',
        'ruddy',
        'obnoxious',
        'careless',
        'robust',
        'future',
        'foamy',
        'perfect',
        'numerous',
        'ultra',
        'bad',
        'racial',
        'receptive',
        'ubiquitous',
        'bustling',
        'puffy',
        'pointless',
        'flawless',
        'scary',
        'elated',
        'vacuous',
        'married',
        'healthy',
        'nippy',
        'steady',
        'hulking',
        'unaccountable',
        'kindly',
        'minor',
        'second',
        'necessary',
        'hungry',
        'vigorous',
        'large',
        'quizzical',
        'intelligent',
        'five',
        'fretful',
        'aback',
        'disillusioned',
        'crazy',
        'nifty',
        'fanatical',
        'nice',
        'unique',
        'frightening',
        'cut',
        'faithful',
        'young',
        'white',
        'conscious',
        'cheap',
        'lumpy',
        'venomous',
        'clear',
        'scattered',
        'new',
        'direful',
        'clean',
        'busy',
        'narrow',
        'recondite',
        'spurious',
        'cooperative',
        'ruthless',
        'excited',
        'excellent',
        'halting',
        'frightened',
        'calm',
        'gratis',
        'safe',
        'skillful',
        'momentous',
        'full',
        'verdant',
        'flowery',
        'beautiful',
        'eight',
        'aloof',
        'broken',
        'rebel',
        'inquisitive',
        'painful',
        'abaft',
        'unsuitable',
        'devilish',
        'homeless',
        'grandiose',
        'offbeat',
        'premium',
        'various',
        'yielding',
        'tiny',
        'bite',
        'beneficial',
        'splendid',
        'probable',
        'courageous',
        'abject',
        'elegant',
        'gullible',
        'whimsical',
        'average',
        'noxious',
        'threatening',
        'glorious',
        'nostalgic',
        'equal',
        'vengeful',
        'gruesome',
        'needy',
        'therapeutic',
        'aberrant',
        'uptight',
        'smiling',
        'chief',
        'friendly',
        'soft',
        'modern',
        'abortive',
        'shy',
        'determined',
        'internal',
        'enchanting',
        'mellow',
        'dark',
        'hanging',
        'high',
        'bent',
        'sharp',
        'remarkable',
        'belligerent',
        'observant',
        'four',
        'acrid',
        'cool',
        'maddening',
        'separate',
        'furtive',
        'windy',
        'pink',
        'watery',
        'nonstop',
        'psychedelic',
        'abiding',
        'rich',
        'juicy',
        'lively',
        'sordid',
        'tender',
        'barbarous',
        'icky',
        'living',
        'funny',
        'lamentable',
        'fascinated',
        'pleasant',
        'tame',
        'heady',
        'blue',
        'messy',
        'ratty',
        'fixed',
        'foregoing',
        'imported',
        'quarrelsome',
        'whole',
        'crowded',
        'past',
        'jolly',
        'omniscient',
        'adamant',
        'feeble',
        'puny',
        'helpful',
        'wholesale',
        'alleged',
        'enormous',
        'salty',
        'capricious',
        'sulky',
        'wonderful',
        'hysterical',
        'chemical',
        'lonely',
        'long',
        'roasted',
        'tedious',
        'defiant',
        'female',
        'frail',
        'superficial',
        'tightfisted',
        'petite',
        'judicious',
        'defeated',
        'meaty',
        'lucky',
        'calculating',
        'righteous',
        'deep',
        'resolute',
        'naughty',
        'squealing',
        'ugly',
        'bitter',
        'godly',
        'best',
        'half',
        'undesirable',
        'energetic',
        'disturbed',
        'lush',
        'illustrious',
        'majestic',
        'normal',
        'exultant',
        'disagreeable',
        'harsh',
        'lively',
        'glib',
        'mountainous',
        'six',
        'natural',
        'unbiased',
        'deadpan',
        'thin',
        'tense',
        'dysfunctional',
        'electric',
        'fluffy',
        'accurate',
        'lacking',
        'cute',
        'wooden',
        'legal',
        'overrated',
        'harmonious',
        'guttural',
        'fragile',
        'wrathful',
        'knotty',
        'earsplitting',
        'noiseless',
        'medical',
        'unkempt',
        'ancient',
        'violent',
        'tacit',
        'mixed',
        'greedy',
        'unable',
        'witty',
        'nebulous',
        'low',
        'literate',
        'slippery',
        'whispering',
        'panicky',
        'highfalutin',
        'exclusive',
        'taboo',
        'waggish',
        'oceanic',
        'aware',
        'disgusted',
        'berserk',
        'dusty',
        'second',
        'icy',
        'heavy',
        'dynamic',
        'solid',
        'axiomatic',
        'sneaky',
        'cautious',
        'didactic',
        'afraid',
        'clammy',
        'soggy',
        'impartial',
        'stale',
        'workable',
        'material',
        'animated',
        'untidy',
        'pricey',
        'testy',
        'parsimonious',
        'numberless',
        'giant',
        'purple',
        'freezing',
        'macabre',
        'malicious',
        'gusty',
        'good',
        'innate',
        'lavish',
        'evasive',
        'hideous',
        'zippy',
        'overwrought',
        'small',
        'damaging',
        'fuzzy',
        'hospitable',
        'confused',
        'useful',
        'knowledgeable',
        'public',
        'gaudy',
        'troubled',
        'better',
        'little',
        'sweltering',
        'descriptive',
        'aboard',
        'gleaming',
        'chunky',
        'greasy',
        'spicy',
        'quixotic',
        'tense',
        'mere',
        'opposite',
        'permissible',
        'skinny',
        'truculent',
        'quickest',
        'redundant',
        'obscene',
        'erratic',
        'delightful',
        'mammoth',
        'wanting',
        'general',
        'inexpensive',
        'brown',
        'alike',
        'misty',
        'oval',
        'furry',
        'nutty',
        'optimal',
        'nervous',
        'poor',
        'bashful',
        'unwritten',
        'efficacious',
        'understood',
        'rapid',
        'mature',
        'possible',
        'three',
        'green',
        'wakeful',
        'actually',
        'madly',
        'alcoholic',
        'far',
        'null',
        'blushing',
        'piquant',
        'hellish',
        'awesome',
        'cold',
        'cumbersome',
        'nappy',
        'stereotyped',
        'absorbing',
        'educated',
        'jobless',
        'willing',
        'enthusiastic',
        'tacky',
        'rural',
        'tall',
        'stimulating',
        'youthful',
        'hapless',
        'adaptable',
        'amused',
        'standing',
        'helpless',
        'rude',
        'important',
        'shiny',
        'needless',
        'cagey',
        'alive',
        'panoramic',
        'square',
        'terrific',
        'subdued',
        'free',
        'thick',
        'unadvised',
        'slimy',
        'subsequent',
        'strong',
        'somber',
        'festive',
        'breakable',
        'dramatic',
        'brash',
        'ludicrous',
        'sedate',
        'hurt',
        'prickly',
        'vivacious',
        'same',
        'keen',
        'sour',
        'seemly',
        'relieved',
        'moaning',
        'spiteful',
        'angry',
        'parallel',
        'utter',
        'versed',
        'black',
        'dusty',
        'flashy',
        'gigantic',
        'diligent',
        'quirky',
        'silent',
        'weary',
        'early',
        'rightful',
        'two',
        'complete',
        'hateful',
        'curly',
        'massive',
        'boring',
        'finicky',
        'concerned',
        'foolish',
        'spiky',
        'unbecoming',
        'neat',
        'lovely',
        'succinct',
        'jumbled',
        'silly',
        'ready',
        'overconfident',
        'changeable',
        'adventurous',
        'ahead',
        'reflective',
        'fortunate',
        'amazing',
        'tight',
        'ad',
        'grotesque',
        'neighborly',
        'billowy',
        'bumpy',
        'organic',
        'selective',
        'penitent',
        'wicked',
        'smooth',
        'special',
        'light',
        'obsequious',
        'erect',
        'smoggy',
        'absurd',
        'boorish',
        'honorable',
        'staking',
        'hallowed',
        'giddy',
        'alert',
        'orange',
        'awful',
        'economic',
        'talented',
        'dizzy',
        'ambitious',
        'uninterested',
        'grubby',
        'pretty',
        'callous',
        'wrong',
        'nonchalant',
        'muddled',
        'deeply',
        'uttermost',
        'fair',
        'thankful',
        'impossible',
        'warlike',
        'voracious',
        'questionable',
        'dull',
        'psychotic',
        'first',
        'adhesive',
        'productive',
        'irate',
        'damaged',
        'wacky',
        'burly',
        'great',
        'dapper',
        'automatic',
        'domineering',
        'quack',
        'bizarre',
        'zonked',
        'sore',
        'childlike',
        'breezy',
        'trashy',
        'sloppy',
        'tasteful',
        'makeshift',
        'teeny',
        'imperfect',
        'divergent',
        'loutish',
        'lyrical',
        'onerous',
        'uneven',
        'toothsome',
        'alluring',
        'purring',
        'selfish',
        'doubtful',
        'few',
        'grouchy',
        'aquatic',
        'blue',
        'sore',
        'third',
        'elfin',
        'boiling',
        'decorous',
        'draconian',
        'ajar',
        'fast',
        'sleepy',
        'attractive',
        'zesty',
        'tricky',
        'crooked',
        'successful',
        'old',
        'late',
        'imminent',
        'lame',
        'befitting',
        'spotted',
        'innocent',
        'lethal',
        'secret',
        'sincere',
        'scared',
        'regular',
        'proud',
        'oafish',
        'equable',
        'weak',
        'stingy',
        'zany',
        'abusive',
        'overt',
        'eminent',
        'acid',
        'tangy',
        'outgoing',
        'pale',
        'shut',
        'towering',
        'protective',
        'simple',
        'worried',
        'tough',
        'short',
        'coherent',
        'rainy',
        'shaggy',
        'brief',
        'abundant',
        'temporary',
        'even',
        'shallow',
        'horrible',
        'nondescript',
        'combative',
        'rustic',
        'tan',
        'pastoral',
        'amuck',
        'functional',
        'savory',
        'immense',
        'daily',
        'bouncy',
        'labored',
        'ragged',
        'shivering',
        'absent',
        'imaginary',
        'wet',
        'ordinary',
        'pumped',
        'unequaled',
        'ambiguous',
        'agreeable',
        'roomy',
        'abhorrent',
        'idiotic',
        'hard',
        'humorous',
        'trite',
        'fat',
        'thoughtless',
        'interesting',
        'military',
        'unequal',
        'spiritual',
        'extra',
        'dreary',
        'eatable',
        'placid',
        'vague',
        'open',
        'plausible',
        'defective',
        'lying',
        'demonic',
        'flagrant',
        'careful',
        'mysterious',
        'yummy',
        'bored',
        'happy',
        'lewd',
        'deafening',
        'depressed',
        'creepy',
        'bright',
        'spooky',
        'phobic',
        'rhetorical',
        'annoying',
        'grieving',
        'guiltless',
        'classy',
        'ablaze',
        'aromatic',
        'right',
        'endurable',
        'gray',
        'obtainable',
        'certain',
        'warm',
        'vast',
        'nimble',
        'satisfying',
        'repulsive',
        'dependent',
        'anxious',
        'stormy',
        'humdrum',
        'ritzy',
        'unknown',
        'woozy',
        'loud',
        'sable',
        'bright',
        'ill',
        'abandoned',
        'upset',
        'gifted',
        'utopian',
        'dear',
        'broad',
        'well',
        'clumsy',
        'condemned',
        'colossal',
        'grumpy',
        'unwieldy',
        'silent',
        'filthy',
        'heartbreaking',
        'stiff',
        'cynical',
        'irritating',
        'macho',
        'scarce',
        'shaky',
        'well',
        'slow',
        'exotic',
        'tiresome',
        'loose',
        'kindhearted',
        'glossy',
        'yellow',
        'chivalrous',
        'flaky',
        'rough',
        'paltry',
        'spotty',
        'acceptable',
        'limping',
        'fierce',
        'nine',
        'petite',
        'jumpy',
        'ignorant',
        'rabid',
        'grey',
        'male',
        'worthless',
        'quaint',
        'synonymous',
        'dazzling',
        'miniature',
        'well',
        'handsome',
        'adjoining',
        'obedient',
        'mighty',
        'tart',
        'long',
        'spectacular',
        'puzzling',
        'silky',
        'feigned',
        'inconclusive',
        'unused',
        'tenuous',
        'incredible',
        'illegal',
        'acoustic',
        'detailed',
        'graceful',
        'sassy',
        'bewildered',
        'scandalous',
        'odd',
        'teeny',
        'lopsided',
        'itchy',
        'heavenly',
        'jealous',
        'left',
        'aboriginal',
        'wandering',
        'possessive',
        'snobbish',
        'exuberant',
        'melted',
        'ripe',
        'tested',
        'jagged',
        'magenta',
        'goofy',
        'romantic',
        'difficult',
        'elderly',
        'flippant',
        'nosy',
        'present',
        'guarded',
        'frantic',
        'accessible',
        'groovy',
        'real',
        'common',
        'incandescent',
        'quick',
        'coordinated',
        'mute',
        'gorgeous',
        'boundless',
        'unruly',
        'swift',
        'mean',
        'last',
        'delicate',
        'auspicious',
        'wiggly',
        'unusual',
        'rampant',
        'delirious',
        'unarmed',
        'disastrous',
        'fancy',
        'political',
        'annoyed',
        'used',
        'sick',
        'ten',
        'clever',
        'flat',
        'brainy',
        'sudden',
        'different',
        'incompetent',
        'charming',
        'one',
        'wistful',
        'holistic',
        'magical',
        'sophisticated',
        'acidic',
        'curvy',
        'faded',
        'mindless',
        'ill',
        'tired',
        'abashed',
        'cruel',
        'elite',
        'naive',
        'faint',
        'periodic',
        'cheerful',
        'straight',
        'simplistic',
        'arrogant',
        'thoughtful',
        'futuristic',
        'awake',
        'swanky',
        'gabby',
        'encouraging',
        'available',
        'fearful',
        'noisy',
        'handy',
        'serious',
        'slim',
        'abounding',
        'sticky',
        'instinctive',
        'responsible',
        'wretched',
        'luxuriant',
        'fearless',
        'superb',
        'shrill',
        'earthy',
        'sweet',
        'uppity',
        'statuesque',
        'far',
        'astonishing',
        'parched',
        'miscreant',
        'exciting',
        'round',
        'ossified',
        'expensive',
        'abstracted',
        'curious',
        'fresh',
        'dashing',
        'extra',
        'gainful',
        'moldy',
        'plant',
        'snotty',
        'flimsy',
        'pathetic',
        'fine',
        'shocking',
        'cute',
        'jaded',
        'fantastic',
        'laughable',
        'stupid',
        'hushed',
        'vagabond',
        'tearful',
        'maniacal',
        'agonizing',
        'nauseating',
        'outstanding',
        'wise',
        'aspiring',
        'sparkling',
        'able',
        'like',
        'painstaking',
        'faulty',
        'loving',
        'handsomely',
        'strange',
        'hot',
        'unsightly',
        'complex',
        'deranged',
        'hypnotic',
        'homely',
        'discreet',
        'unhealthy',
        'dirty',
        'learned',
        'sturdy',
        'crabby',
        'precious',
        'hissing',
        'curved',
        'sad',
        'efficient',
        'hard',
        'hurried',
        'violet',
        'wide',
        'scientific',
        'thirsty',
        'cloistered',
        'fluttering',
        'squalid',
        'amusing',
        'assorted',
        'overjoyed',
        'old',
        'gamy',
        'hilarious',
        'merciful',
        'dispensable',
        'substantial',
        'glamorous',
        'many',
        'plucky',
        'knowing',
        'murky',
        'evanescent',
        'jittery',
        'garrulous',
        'juvenile',
        'torpid',
        'cowardly',
        'upbeat',
        'level',
        'abnormal',
        'obese',
        'steadfast',
        'rambunctious',
        'puzzled',
        'reminiscent',
        'uncovered',
        'absorbed',
        'gentle',
        'thundering',
        'physical',
        'voiceless',
        'gaping',
        'ceaseless',
        'cuddly',
        'volatile',
        'husky',
        'thirsty',
        'deserted',
        'pushy',
        'spiffy',
        'adorable',
        'zealous',
        'steep',
        'fabulous',
        'womanly',
        'envious',
        'tasteless',
        'wasteful',
        'caring',
        'melodic',
        'drab',
        'poised',
        'victorious',
        'grateful',
        'private',
        'distinct',
        'obeisant',
        'mundane',
        'picayune',
        'profuse',
        'known',
        'familiar',
        'fertile',
        'invincible',
        'perpetual',
        'royal',
        'stupendous',
        'joyous',
        'craven',
        'typical',
        'red',
        'useless',
        'wary',
        'kind',
        'brawny',
        'obsolete',
        'enchanted',
        'ugliest',
        'tranquil',
        'cultured',
        'secretive',
        'delicious',
        'glistening',
        'languid',
        'nasty',
        'symptomatic',
        'accidental',
        'resonant',
        'dry',
        'cluttered',
        'habitual',
        'comfortable',
        'plain',
        'scrawny',
        'smelly',
        'industrious',
        'brave',
        'decisive',
        'abrupt',
        'capable',
        'likeable',
        'chubby',
        'tawdry',
        'smart',
        'embarrassed',
        'longing',
        'eager',
        'high',
        'wide',
        'near',
        'famous',
        'ashamed'
    ]
    return prefix + secrets.choice(adjectives) + suffix