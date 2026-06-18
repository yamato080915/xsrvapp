function adjustScale() {
	const contestname = document.getElementById("contestname");
	contestname.style.whiteSpace = "normal";
	width = contestname.offsetWidth;
	contestname.style.whiteSpace = "nowrap";
	width2 = contestname.offsetWidth;
	scale = width/width2;
	contestname.style.transform = `scaleX(${scale})`;
	contestname.style.transformOrigin = 'left';
}
window.addEventListener("load", adjustScale);
window.addEventListener("resize", adjustScale);
function createRatingChart(url, chart_id, rating_id, place_id, diff_id, endtime_id, contestname_id, a_id, div_id) {
	fetch(url)
	.then(response => response.json())
	.then(data => {
		const ratings = data.map(contest => contest.NewRating);
		const performances = data.map(contest => contest.Performance);
		const dates = data.map(contest => new Date(contest.EndTime));
		const firstDate = new Date(dates[0]);
		firstDate.setMonth(firstDate.getMonth() - 1);
		const lastDate = new Date(dates[dates.length - 1]);
		lastDate.setMonth(lastDate.getMonth() + 1);
		const Max = Math.max(...ratings.concat(performances))
		const yMax = Math.ceil((Max + 100) / 200) * 200;
		const ctx = document.getElementById(chart_id).getContext('2d');
		const backgroundColors = [
			{ color: 'rgba(128,128,128,0.3)', max: 399 },
			{ color: 'rgba(128,64,0,0.3)', max: 799 },
			{ color: 'rgba(0,128,0,0.3)', max: 1199 },
			{ color: 'rgba(0,192,192,0.3)', max: 1599 },
			{ color: 'rgba(0,0,255,0.3)', max: 1999 },
			{ color: 'rgba(192,192,0,0.3)', max: 2399 },
			{ color: 'rgba(255,128,0,0.3)', max: 2799 },
			{ color: 'rgba(255,0,0,0.3)', max: 9999 }
		];
		const RatingColors = data.map(contest => {
			if (contest.NewRating<=399) return "#808080";
			if (contest.NewRating<=799) return "#804000";
			if (contest.NewRating<=1199) return "#008000";
			if (contest.NewRating<=1599) return "#00c0c0";
			if (contest.NewRating<=1999) return "#0000ff";
			if (contest.NewRating<=2399) return "#c0c000";
			if (contest.NewRating<=2799) return "#ff8000";
			if (contest.NewRating<=9999) return "#ff0000";
		});
		const PerformanceColors = data.map(contest => {
			if (contest.Performance<=399) return "#808080";
			if (contest.Performance<=799) return "#804000";
			if (contest.Performance<=1199) return "#008000";
			if (contest.Performance<=1599) return "#00c0c0";
			if (contest.Performance<=1999) return "#0000ff";
			if (contest.Performance<=2399) return "#c0c000";
			if (contest.Performance<=2799) return "#ff8000";
			if (contest.Performance<=9999) return "#ff0000";
		});
		const plugin = {
			id: 'rankBackground',
			beforeDraw: chart => {
				const { ctx, chartArea: { top, bottom, left, right }, scales: { y } } = chart;
				backgroundColors.forEach(({ color, max }, i) => {
					const min = i === 0 ? y.min : backgroundColors[i - 1].max + 1;
					const yTop = y.getPixelForValue(Math.min(max, yMax));
					const yBottom = y.getPixelForValue(min);
					ctx.save();
					ctx.beginPath();
					ctx.rect(left, top, right - left, bottom - top);
					ctx.clip();
					ctx.fillStyle = color;
					ctx.fillRect(left, yTop, right - left, yBottom - yTop);
					ctx.restore();
				});
			}
		};
		new Chart(ctx, {
			type: 'line',
			data: {
				labels: dates,
				datasets: [{
					label: 'Rating',
					data: dates.map((d, i) => ({ x: d, y: ratings[i] })),
					borderColor: '#606060',
					backgroundColor: RatingColors,
					fill: false,
					tension: 0.1,
					pointBorderColor: 'white',
					borderWidth: 1,
					pointRadius: 3.5,
					pointHoverRadius: 4
				},{
					label: 'Performance',
					data: dates.map((d, i) => ({ x: d, y: performances[i] })),
					borderColor: 'rgba(255,0,0,0.5)',
					backgroundColor: PerformanceColors,
					fill: false,
					tension: 0.1,
					pointBorderColor: 'white',
					borderWidth: 1,
					pointRadius: 3,
					pointHoverRadius: 4
				}]
			},
			options: {
				responsive: true,
				plugins: {
					legend: {
						display: true,
						labels: {
							generateLabels: function(chart) {
								const original = Chart.defaults.plugins.legend.labels.generateLabels(chart);
								original[0].fillStyle = "rgba(128,128,128,0.3)";
								original[1].fillStyle = "rgba(128,128,128,0.3)";
								return original;
							}
						}
					}
				},
				scales: {
					x: {
						type: 'time',
						time: {
							unit: 'month',
							tooltipFormat: 'MMM yyyy',
							displayFormats: {
								month: 'MMM yyyy'
							}
						},
						min: firstDate,
						max: lastDate,
						title: {
							display: false,
							text: 'Date'
						},
						grid: {
							color: 'rgba(255,255,255,0.3)'
						}
					},
					y: {
						beginAtZero: true,
						min: 0,
						max: yMax,
						title: {
							display: false,
							text: 'Rating'
						},
						ticks: {
							stepSize: 400,
							callback: function(value) {
								const rankBoundaries = [400, 800, 1200, 1600, 2000, 2400, 2800];
								return rankBoundaries.includes(value) ? value : '';
							}
						},
						grid: {
							color: 'rgba(255,255,255,0.3)'
						}
					}
				},
				onHover: (event, chartElement) => {
					const rating = document.getElementById(rating_id);
					const place = document.getElementById(place_id);
					const diff = document.getElementById(diff_id);
					const date = document.getElementById(endtime_id);
					const contestname = document.getElementById(contestname_id);
					const link = document.getElementById(a_id)
					const div = document.getElementById(div_id)
					if (chartElement && chartElement.length > 0) {
						const index = chartElement[0].index;
						const dataPoint = data[index];
						rating.innerText = dataPoint["NewRating"];
						
						rating.classList.remove(...["gray", "brown", "green", "cyan", "blue", "yellow", "orange", "red"]);
						rating.classList.add(dataPoint["Rank"]);
						div.classList.remove(...["grayb", "brownb", "greenb", "cyanb", "blueb", "yellowb", "orangeb", "redb"])
						div.classList.add(String(dataPoint["Rank"]+"b"))
						if (String(dataPoint["Place"]).slice(-1)==1) {
							place.innerText = dataPoint["Place"] + "st";
						} else if (String(dataPoint["Place"]).slice(-1)==2) {
							place.innerText = dataPoint["Place"] + "nd";
						} else if (String(dataPoint["Place"]).slice(-1)==3) {
							place.innerText = dataPoint["Place"] + "rd";
						} else {
							place.innerText = dataPoint["Place"] + "th";
						}
						if (dataPoint["NewRating"] - dataPoint["OldRating"]>0) {
							diff.innerText = "+" + String(dataPoint["NewRating"] - dataPoint["OldRating"]);
						} else {
							diff.innerText = String(dataPoint["NewRating"] - dataPoint["OldRating"]);
						}
						date.innerText = dataPoint["EndTime"];
						contestname.innerText = dataPoint["ContestName"];
						if (a_id == "atcoder-a") {
							link.setAttribute("href", "https://atcoder.jp/contests/" + String(dataPoint["ContestScreenName"]).split(".")[0] + "/standings?watching=Yamato0915");
						} else {
							link.setAttribute("href", "https://onlinemathcontest.com/contests/" + String(dataPoint['ContestScreenName']).split('.')[0])
						}
						//ここから長体を調整
						adjustScale();
					}
				}
			},
			plugins: [plugin]
		});
	});
}