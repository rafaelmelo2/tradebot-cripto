// Configurações personalizáveis
const config = {
  websocketUrl: 'wss://testnet.binance.vision/ws/btcusdt@trade', // URL do WebSocket
  maxDataPoints: 60, // Número máximo de pontos no gráfico
  updateInterval: 1000, // Intervalo de atualização (ms)
  maxLineOrders: 10,
  chart: {
    width: 1200, // Largura do gráfico
    height: 400, // Altura do gráfico
    margin: { top: 20, right: 60, bottom: 30, left: 50 }, // Margens internas
    lineColor: 'blue', // Cor da linha do gráfico
    lineWidth: 2, // Espessura da linha do gráfico
    yPadding: 100, // Espaço adicional no eixo Y
  },
};

// Variáveis globais para armazenar os dados
let prices = []; // Lista de preços
let timestamps = []; // Lista de timestamps
let lastUpdateTime = Date.now(); // Controle de atualização do gráfico

// Elementos do DOM
const priceDisplay = document.getElementById("current-price"); // Div com o preço atual
const ordersTable = document.getElementById("orders-table-body"); // Corpo da tabela para exibir ordens

// Configuração do gráfico com D3.js
const { width, height, margin, lineColor, lineWidth, yPadding } = config.chart;

// Dimensões do SVG
const svgWidth = width;
const svgHeight = height;

// Criação do SVG e do grupo interno para o gráfico
const svg = d3.select("#chart")
  .append("svg")
  .attr("width", svgWidth)
  .attr("height", svgHeight);

const g = svg.append("g")
  .attr("transform", `translate(${margin.left},${margin.top})`);

// Adiciona marcador para o preço atual no gráfico
const priceMarker = g.append("text")
  .attr("class", "price-marker")
  .style("fill", "black")
  .style("font-size", "12px")
  .style("font-weight", "bold");

const priceCircle = g.append("circle")
  .attr("class", "price-circle")
  .attr("r", 5)
  .style("fill", "red");

// Largura e altura internas do gráfico
const innerWidth = svgWidth - margin.left - margin.right;
const innerHeight = svgHeight - margin.top - margin.bottom;

// Escalas do gráfico
const xScale = d3.scaleTime().range([0, innerWidth]);
const yScale = d3.scaleLinear().range([innerHeight, 0]);

// Linha do gráfico
const line = d3.line()
  .x((d, i) => xScale(timestamps[i]))
  .y((d) => yScale(d));

// Adiciona o caminho da linha ao gráfico
g.append("path")
  .attr("class", "line")
  .style("fill", "none")
  .style("stroke", lineColor)
  .style("stroke-width", `${lineWidth}px`);

// Adiciona os eixos X e Y ao gráfico
g.append("g").attr("class", "x-axis").attr("transform", `translate(0,${innerHeight})`);
g.append("g").attr("class", "y-axis");

// Atualiza o gráfico com novos dados
function updateChart() {
  if (timestamps.length === 0 || prices.length === 0) return; // Verifica se há dados

  // Atualiza as escalas com os novos dados
  xScale.domain(d3.extent(timestamps));
  yScale.domain([d3.min(prices) - yPadding, d3.max(prices) + yPadding]);

  // Atualiza a linha com os dados mais recentes
  g.select(".line")
    .datum(prices)
    .attr("d", line);

  // Atualiza os eixos
  g.select(".x-axis").call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%H:%M:%S")));
  g.select(".y-axis").call(d3.axisLeft(yScale));

  // Atualiza o marcador de preço na ponta do gráfico
  const lastPrice = prices[prices.length - 1];
  const lastTimestamp = timestamps[timestamps.length - 1];
  const xPosition = xScale(lastTimestamp);
  const yPosition = yScale(lastPrice);

  // Posiciona o círculo no último ponto
  priceCircle
    .attr("cx", xPosition)
    .attr("cy", yPosition);

  // Posiciona o texto próximo ao círculo
  priceMarker
    .attr("x", xPosition + 5) // Desloca levemente para a direita
    .attr("y", yPosition - 5) // Desloca levemente para cima
    .text(`${lastPrice.toFixed(2)} USDT`);
}

// Conecta ao WebSocket da Binance
const ws = new WebSocket(config.websocketUrl);

// Evento chamado quando uma nova mensagem é recebida pelo WebSocket
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Extrai o preço e o timestamp da mensagem
  const isBuy = !data.m;
  const price = parseFloat(data.p); // Preço
  const timestamp = new Date(data.T); // Timestamp legível
  const volume = parseFloat(data.q); // Volume negociado

  // Atualiza o preço atual na tela
  priceDisplay.textContent = `Preço Atual: ${price.toFixed(2)} USDT`;

  // Adiciona o preço e o timestamp às listas
  prices.push(price);
  timestamps.push(timestamp);

  // Remove os dados mais antigos se exceder o limite
  if (prices.length > config.maxDataPoints) prices.shift();
  if (timestamps.length > config.maxDataPoints) timestamps.shift();

  // Adiciona uma nova linha na tabela de ordens
  const newRow = document.createElement("tr");
  newRow.innerHTML = `
    <td>${isBuy ? "Compra" : "Venda"}</td>
    <td>${timestamp.toLocaleTimeString()}</td>
    <td>${price.toFixed(2)} USDT</td>
    <td>${volume.toFixed(6)}</td>
  `;
  ordersTable.prepend(newRow); // Adiciona no topo da tabela

  // Limita o número de linhas exibidas na tabela
  if (ordersTable.rows.length > config.maxLineOrders) {
    ordersTable.deleteRow(-1); // Remove a última linha
  }

  // Atualiza o gráfico em intervalos controlados
  const now = Date.now();
  if (now - lastUpdateTime >= config.updateInterval) {
    updateChart();
    lastUpdateTime = now;
  }
};
