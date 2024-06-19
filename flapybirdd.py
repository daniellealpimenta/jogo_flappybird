import pygame
import os
import random
import neat
import threading

ai_jogando = False
geracao = 0

TELA_LARGURA = 570
TELA_ALTURA = 954

IMAGEM_BEGIN = (pygame.image.load(os.path.join('Imagens', 'tela_begin.jpg')))
IMAGEM_END = (pygame.image.load(os.path.join('Imagens', 'tela_quando_perde.jpg')))
IMAGEM_END_NO = (pygame.image.load(os.path.join('Imagens', 'tela_quando_perde_no.jpg')))
IMAGEM_END_YES = (pygame.image.load(os.path.join('Imagens', 'tela_quando_perde_yes.jpg')))
IMAGEM_PAUSADO = (pygame.image.load(os.path.join('Imagens', 'tela_pausado.jpg')))
IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'base.png')))
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'bg.png')))
IMAGENS_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('Imagens', 'bird3.png'))),
]

pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 50)

class Passaro:
    IMGS = IMAGENS_PASSARO
    # animações da rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self):
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # calcular o deslocamento
        self.tempo += 1
        deslocamento = 1.5 * (self.tempo**2) + self.velocidade * self.tempo

        # restringir o deslocamento
        if deslocamento > 16:
            deslocamento = 16
        elif deslocamento < 0:
            deslocamento -= 2

        self.y += deslocamento

        # o angulo do passaro
        if deslocamento < 0 or self.y < (self.altura + 50):
            if self.angulo < self.ROTACAO_MAXIMA:
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # definir qual imagem do passaro vai usar
        self.contagem_imagem += 1

        if self.contagem_imagem < self.TEMPO_ANIMACAO:
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*2:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*3:
            self.imagem = self.IMGS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO*4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem >= self.TEMPO_ANIMACAO*4 + 1:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0

        # se o passaro tiver caindo eu não vou bater asa
        if self.angulo <= -80:
            self.imagem = self.IMGS[1]
            self.contagem_imagem = self.TEMPO_ANIMACAO*2

        # desenhar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.imagem)

class Cano:
    DISTANCIA = 200
    VELOCIDADE = 5
    INCREMENTO_VELOCIDADE = 2  # Novo atributo para incrementar a velocidade

    def __init__(self, x):
        self.x = x
        self.altura = 0
        self.pos_topo = 0
        self.pos_base = 0
        self.CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)
        self.CANO_BASE = IMAGEM_CANO
        self.passou = False
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(40, 450)
        self.pos_topo = self.altura - self.CANO_TOPO.get_height()
        self.pos_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def desenhar(self, tela):
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y))
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))

        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)
        base_ponto = passaro_mask.overlap(base_mask, distancia_base)

        if topo_ponto or base_ponto:
            return True
        return False

    @classmethod
    def aumentar_velocidade(cls, pontuacao):
        if pontuacao % 5 == 0:
            cls.VELOCIDADE += cls.INCREMENTO_VELOCIDADE

    @classmethod
    def resetar_velocidade(cls):
        cls.VELOCIDADE = 5


class Chao:
    VELOCIDADE = 5
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.LARGURA

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))

def desenhar_tela(tela, passaros, canos, chao, pontos):
    tela.blit(IMAGEM_BACKGROUND, (0, 0))
    for passaro in passaros:
        passaro.desenhar(tela)
    for cano in canos:
        cano.desenhar(tela)

    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

    if ai_jogando:
        texto = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()

def tela_inicio(tela):
    rodando = True
    while rodando:
        tela.blit(IMAGEM_BEGIN, (0, 0))
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_s:
                    rodando = False

def tela_pausada(tela):
    pausado = True
    while pausado:
        tela.blit(IMAGEM_PAUSADO, (0, 0))
        pygame.display.update()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:  # Verificação de tipo de evento
                if evento.key == pygame.K_p:  # Verificação da tecla pressionada
                    pausado = False


def tela_fim(tela, pontos):
    fim = True
    escolha = 0  # 0 para esquerda, 1 para direita
    while fim:
        tela.blit(IMAGEM_END, (0, 0))
        texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
        tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

        if escolha == 0:
            tela.blit(IMAGEM_END_YES, (0, 0))
        else:
            tela.blit(IMAGEM_END_NO, (0, 0))

        pygame.display.update()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                quit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_LEFT:
                    escolha = 0
                elif evento.key == pygame.K_RIGHT:
                    escolha = 1
                elif evento.key == pygame.K_RETURN:
                    if escolha == 0:
                        fim = False
                    elif escolha == 1:
                        pygame.quit()
                        quit()

def main(genomas, config):
    global geracao
    geracao += 1

    redes = []
    lista_genomas = []
    passaros = [Passaro(230, 350)]

    if ai_jogando:
        passaros = []
        for _, genoma in genomas:
            rede = neat.nn.FeedForwardNetwork.create(genoma, config)
            redes.append(rede)
            genoma.fitness = 0
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))

    chao = Chao(730)
    canos = [Cano(700)]
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    pontos = 0
    relogio = pygame.time.Clock()

    # Tela de início
    if not ai_jogando:
        tela_inicio(tela)

    rodando = True
    while rodando:
        relogio.tick(30)

        # interação com o usuário
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not ai_jogando:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        for passaro in passaros:
                            passaro.pular()
                    if evento.key == pygame.K_p:
                        tela_pausada(tela)

        indice_cano = 0
        if len(passaros) > 0:
            if len(canos) > 1 and passaros[0].x > (canos[0].x + canos[0].CANO_TOPO.get_width()):
                indice_cano = 1
        else:
            rodando = False
            break

        # mover as coisas
        for i, passaro in enumerate(passaros):
            passaro.mover()
            if ai_jogando:
                lista_genomas[i].fitness += 0.1
                output = redes[i].activate((passaro.y,
                                            abs(passaro.y - canos[indice_cano].altura),
                                            abs(passaro.y - canos[indice_cano].pos_base)))
                if output[0] > 0.5:
                    passaro.pular()
        chao.mover()

        adicionar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):
                    passaros.pop(i)
                    if ai_jogando:
                        lista_genomas[i].fitness -= 1
                        lista_genomas.pop(i)
                        redes.pop(i)
                    if not ai_jogando or len(passaros) == 0:
                        Cano.resetar_velocidade()  # Resetar a velocidade ao colidir com o último pássaro
                if not cano.passou and passaro.x > cano.x:
                    cano.passou = True
                    adicionar_cano = True
            cano.mover()
            if cano.x + cano.CANO_TOPO.get_width() < 0:
                remover_canos.append(cano)

        if adicionar_cano:
            pontos += 1
            canos.append(Cano(600))
            if ai_jogando:
                for genoma in lista_genomas:
                    genoma.fitness += 5
            Cano.aumentar_velocidade(pontos)  # Chamar a função para aumentar a velocidade

        for cano in remover_canos:
            canos.remove(cano)

        # Verificar se o pássaro colide com o chão ou vai para fora da tela
        passaros_a_remover = []
        for i, passaro in enumerate(passaros):
            if (passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y < 0:
                passaros_a_remover.append(i)

        for i in reversed(passaros_a_remover):
            passaros.pop(i)
            if ai_jogando:
                lista_genomas.pop(i)
                redes.pop(i)
            if not ai_jogando or len(passaros) == 0:
                Cano.resetar_velocidade()  # Resetar a velocidade ao colidir com o último pássaro

        desenhar_tela(tela, passaros, canos, chao, pontos)

    # Tela de fim
    if not ai_jogando:
        tela_fim(tela, pontos)

def rodar(caminho_config):
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                caminho_config)

    populacao = neat.Population(config)
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    if ai_jogando:
        populacao.run(main, 50)
    else:
        while True:
            main(None, None)

if __name__ == '__main__':
    caminho = os.path.dirname(__file__)
    caminho_config = os.path.join(caminho, 'config.txt')
    pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    tela_inicio(pygame.display.get_surface())
    rodar(caminho_config)
