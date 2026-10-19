(function (window, L) {
  'use strict';

  function verificarRespostas(camada) {
    // Uma resposta HTTP 403 pode conter uma imagem válida e disparar "load".
    // Verificamos o status antes de entregar a imagem ao Leaflet.
    camada.createTile = function (coords, done) {
      var tile = document.createElement('img');
      var cancelamento = new AbortController();
      var blobUrl;
      tile.alt = '';
      tile.setAttribute('role', 'presentation');

      function liberarImagem() {
        if (blobUrl) {
          window.URL.revokeObjectURL(blobUrl);
          blobUrl = null;
        }
      }

      tile.cancelarCarregamento = function () {
        cancelamento.abort();
        tile.onload = null;
        tile.onerror = null;
        liberarImagem();
      };
      function concluir(erro) {
        liberarImagem();
        if (!cancelamento.signal.aborted) {
          done(erro, tile);
        }
      }
      tile.onload = function () {
        concluir(null);
      };
      tile.onerror = function () {
        concluir(new Error('Não foi possível ler a imagem do mapa.'));
      };

      // O navegador mantém seu cache HTTP e envia o Referer da página.
      window.fetch(this.getTileUrl(coords), {signal: cancelamento.signal})
        .then(function (resposta) {
          if (!resposta.ok) {
            throw new Error('Mapa indisponível: HTTP ' + resposta.status);
          }
          return resposta.blob();
        })
        .then(function (blob) {
          if (!cancelamento.signal.aborted) {
            blobUrl = window.URL.createObjectURL(blob);
            tile.src = blobUrl;
          }
        })
        .catch(function (erro) {
          concluir(erro);
        });
      return tile;
    };
    camada.on('tileunload', function (evento) {
      evento.tile.cancelarCarregamento();
    });
    return camada;
  }

  // Configuração compartilhada pelas páginas de doenças e de comparação.
  function criarMapasBase() {
    var arquivoLocal = window.location.protocol === 'file:';
    var semFundo = L.layerGroup();
    var camadas = {};

    if (!arquivoLocal) {
      camadas.Ruas = verificarRespostas(L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }));
      camadas['Imagem de satélite'] = verificarRespostas(L.tileLayer.provider('Esri.WorldImagery', {
        maxZoom: 19
      }));
    }
    camadas['Sem mapa de fundo'] = semFundo;

    function acompanhar(map) {
      var aviso = L.control({position: 'topright'});
      var mensagem = '';
      var trocaPendente;

      aviso.onAdd = function () {
        var div = L.DomUtil.create('div', 'mapa-aviso');
        div.setAttribute('role', 'status');
        div.textContent = mensagem;
        L.DomEvent.disableClickPropagation(div);
        L.DomEvent.disableScrollPropagation(div);
        return div;
      };

      function mostrarAviso(texto) {
        mensagem = texto;
        aviso.remove();
        aviso.addTo(map);
      }

      map.on('baselayerchange', function () {
        aviso.remove();
      });
      map.on('unload', function () {
        window.clearTimeout(trocaPendente);
      });

      Object.keys(camadas).forEach(function (nome) {
        var camada = camadas[nome];
        if (camada === semFundo) {
          return;
        }
        camada.on('tileerror', function (evento) {
          // Oculta a imagem de erro e mantém as camadas de dados utilizáveis.
          evento.tile.style.visibility = 'hidden';
          if (!map.hasLayer(camada)) {
            return;
          }
          window.clearTimeout(trocaPendente);
          trocaPendente = window.setTimeout(function () {
            if (!map.hasLayer(camada)) {
              return;
            }
            map.removeLayer(camada);
            semFundo.addTo(map);
            mostrarAviso('O mapa de fundo não carregou. Os dados continuam disponíveis. ' +
              'Verifique a conexão e selecione Ruas ou Imagem de satélite no controle de camadas para tentar novamente.');
          }, 0);
        });
      });

      if (arquivoLocal) {
        mostrarAviso('Para carregar o mapa de fundo, abra INICIAR_WINDOWS.bat na pasta do sistema. ' +
          'Use a página que será aberta no navegador.');
      } else if (window.navigator.onLine === false) {
        mostrarAviso('Sem conexão com a internet. Os dados continuam disponíveis. ' +
          'Quando a conexão voltar, selecione um mapa de fundo no controle de camadas.');
      }
    }

    return {
      camadas: camadas,
      inicial: arquivoLocal || window.navigator.onLine === false ? semFundo : camadas.Ruas,
      acompanhar: acompanhar
    };
  }

  window.CavalaricaMapas = {criar: criarMapasBase};
}(window, L));
