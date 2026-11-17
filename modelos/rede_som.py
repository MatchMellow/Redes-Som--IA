
import math
import random


class RedeSOM:

    def __init__(
        self,
        linhas,
        colunas,
        dimensoes,
        taxa_aprendizado=0.5,
        sigma=None,
        epocas=30,
        semente=42
    ):

        self.linhas = linhas
        self.colunas = colunas
        self.dimensoes = dimensoes

        self.taxa_inicial = taxa_aprendizado

        self.sigma_inicial = (
            sigma if sigma is not None
            else max(linhas, colunas) / 2
        )

        self.epocas = epocas

        self.historico_erros = []
        self.pesos = []

        # Gerador de números aleatórios com semente fixa. É usado nos
        # pesos iniciais E na ordem dos municípios em cada época, para
        # que o mesmo código com os mesmos dados dê sempre o mesmo mapa.
        self.gerador = random.Random(semente)
        gerador = self.gerador

        # Inicializar os pesos dos neurônios
        for i in range(linhas):

            linha = []

            for j in range(colunas):

                neuronio = [
                    gerador.random()
                    for _ in range(dimensoes)
                ]

                linha.append(neuronio)

            self.pesos.append(linha)

    # Calcular distância euclidiana
    def distancia(self, vetor1, vetor2):

        soma = 0

        for k in range(self.dimensoes):

            diferenca = vetor1[k] - vetor2[k]

            soma += diferenca ** 2

        return math.sqrt(soma)

    # Encontrar o neurônio mais próximo (BMU)
    def encontrar_bmu(self, entrada):

        menor_distancia = float("inf")
        melhor_neuronio = (0, 0)

        for i in range(self.linhas):

            for j in range(self.colunas):

                distancia = self.distancia(
                    entrada,
                    self.pesos[i][j]
                )

                if distancia < menor_distancia:

                    menor_distancia = distancia
                    melhor_neuronio = (i, j)

        return melhor_neuronio

    # Calcular influência da vizinhança
    def vizinhanca(self, distancia_mapa, sigma):

        return math.exp(
            -(distancia_mapa ** 2) /
            (2 * sigma ** 2)
        )

    # Atualizar os pesos
    def atualizar_pesos(
        self,
        entrada,
        bmu,
        taxa,
        sigma
    ):

        bmu_linha, bmu_coluna = bmu

        for i in range(self.linhas):

            for j in range(self.colunas):

                distancia_mapa = math.sqrt(
                    (i - bmu_linha) ** 2 +
                    (j - bmu_coluna) ** 2
                )

                influencia = self.vizinhanca(
                    distancia_mapa,
                    sigma
                )

                for k in range(self.dimensoes):

                    peso = self.pesos[i][j][k]

                    diferenca = entrada[k] - peso

                    self.pesos[i][j][k] += (
                        taxa * influencia * diferenca
                    )

    # Treinar a rede
    def treinar(self, dados, callback=None):

        total = len(dados)

        if total == 0:
            raise ValueError("A base de treinamento está vazia.")

        for epoca in range(self.epocas):

            progresso = epoca / max(1, self.epocas - 1)

            taxa = (
                self.taxa_inicial *
                math.exp(-progresso)
            )

            sigma = (
                self.sigma_inicial *
                math.exp(-progresso)
            )

            ordem = list(range(total))
            # Usa o gerador com semente (antes usava random.shuffle,
            # sem semente, e cada execução gerava um mapa diferente)
            self.gerador.shuffle(ordem)

            erro_total = 0

            for indice in ordem:

                entrada = dados[indice]

                bmu = self.encontrar_bmu(entrada)

                erro_total += self.distancia(
                    entrada,
                    self.pesos[bmu[0]][bmu[1]]
                )

                self.atualizar_pesos(
                    entrada,
                    bmu,
                    taxa,
                    sigma
                )

            erro_medio = erro_total / total

            self.historico_erros.append(erro_medio)

            print(
                f"Época {epoca + 1}/{self.epocas} "
                f"| Erro médio: {erro_medio:.6f}"
            )

            if callback is not None:
                callback(
                    epoca + 1,
                    self.epocas,
                    erro_medio,
                    self
                )

        print("\nTreinamento concluído!")

    # Identificar neurônio vencedor de cada município
    def mapear(self, dados):

        resultados = []

        for entrada in dados:

            bmu = self.encontrar_bmu(entrada)

            resultados.append(bmu)

        return resultados

    # Retornar matriz de pesos
    def obter_pesos(self):

        return self.pesos
