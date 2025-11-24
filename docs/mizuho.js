// ----------------------------------------------------------------------------
// functions
// ----------------------------------------------------------------------------
var Mzh = Mzh || {};

// HTML繧ｿ繧ｰ縺ｮ繧ｨ繧ｹ繧ｱ繝ｼ繝�
Mzh.escHTML = function(str) {
  if(typeof str !== 'string') return str;
  return str.replace(/[&'`"<>]/g, function(match) {
    return {'&': '&amp;', "'": '&#x27;', '`': '&#x60;', '"': '&quot;', '<': '&lt;', '>': '&gt;'}[match];
  });
};

// 蜈�捷繧定･ｿ證ｦ縺ｫ螟画鋤縺吶ｋ髢｢謨ｰ
Mzh.yearConvert = function(str) {
  var mc = str.match(/(?:(?:(蟷ｳ謌酢莉､蜥�)(\d+|蜈�))|(\d{4}))蟷ｴ(\d{1,2})譛�(\d{1,2})譌･/), y;
  if(!mc) return false;
  switch(mc[1]) {
    case '蟷ｳ謌�': y = 1988 + +mc[2];
    break;
    case '莉､蜥�': y = 2018 + +mc[2];
    break;
    default: y = +mc[3];
  }
  return { year: y, month: +mc[4], date: +mc[5] };
};

// 譖懈律繧定ｿ斐☆
Mzh.dayJp = function(day) {
  return ['譌･', '譛�', '轣ｫ', '豌ｴ', '譛ｨ', '驥�', '蝨�'][+day];
};

// 謨ｰ蟄励↓繧ｫ繝ｳ繝槭ｒ蜈･繧後ｋ髢｢謨ｰ
Mzh.insertComma = function(str, slice, option) {
  str = String(str);
  slice = slice || 3;
  option = option || ',';
  if(str.indexOf(',') !== -1) return str;
  return str.replace(/(\d+)(.*)/, function(m, $1, $2) {
    var rx = new RegExp('(\\d)(?=(\\d{' + slice + '})+(?!\\d))', 'g');
    return String($1).replace(rx, '$1' + option) + $2;
  });
};


// ----------------------------------------------------------------------------
// carry over
// ----------------------------------------------------------------------------
(function($) {
    $.fn.carryOver = function() {
      if(!this.length) return false;
      var $this = this, insertComma = Mzh.insertComma,
          path = '/takarakuji/apl/',
          getCarryOver = function(results, type, $box, $prize) {
            var index, prize, splitPrize, i;
            switch(type) {
              case 'loto6': index = 9;
              break;
              case 'loto7': index = 10;
              break;
            }
            // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
            results = results.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
              return String.fromCharCode(str.charCodeAt(0) - 65248);
            });
            prize = parseInt(results.split(/\r\n|\n|\r/)[index].match(/\d+蜀�/));
            if(prize <= 0) {
              $box.css('display', 'none');
            } else {
              splitPrize = insertComma(prize, 4, '_').split('_');
              prize = '';
              for(i = 0; i < splitPrize.length; i++) {
                prize = prize + '<span class="carryover-prize-amount">' + splitPrize[i] + '</span><span class="carryover-prize-unit">' + ['', '蜀�', '荳�', '蜆�'][splitPrize.length - i] + '</span>';
              }
              $prize.html(prize);
              $this.css('display', 'block');
            }
          },
          getLatest = function(type, path, $box, $prize) {
            $.ajax({
              type: 'GET',
              dataType: 'text',
              url: path + 'txt/' + type + '/name.txt?' + (new Date().getTime())
            }).then(
              function(data) {
                var file = data.split(/\r\n|\n|\r/)[1].match(/A\d+.CSV/);
                $.ajax({
                  beforeSend: function(xhr){
                    xhr.overrideMimeType('text/plain;charset=Shift_JIS');
                  },
                  type: 'GET',
                  dataType: 'text',
                  url: '/retail/takarakuji/loto/' + type + '/csv/' + file + '?' + (new Date().getTime())
                }).then(
                  function(data) {
                    getCarryOver(data, type, $box, $prize);
                  },
                  function() {
                    console.log('繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
                  }
                );
              },
              function() {
                console.log('繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
              }
            );
          };
  
      getLatest('loto6', path, $this.find('.js-carryover-loto6'), $this.find('.js-carryover-loto6-prize'));
      getLatest('loto7', path, $this.find('.js-carryover-loto7'), $this.find('.js-carryover-loto7-prize'));
    };
    $(function() {
      $('.js-carryover').carryOver();
    });
  })(jQuery);
  
  (function($) {
      var _ua = (function(u){
          return {
              Mobile:(u.indexOf("windows") != -1 && u.indexOf("phone") != -1)
              || u.indexOf("iphone") != -1
              || u.indexOf("ipod") != -1
              || (u.indexOf("android") != -1 && u.indexOf("mobile") != -1)
              || (u.indexOf("firefox") != -1 && u.indexOf("mobile") != -1)
              || u.indexOf("blackberry") != -1
          }
      })(window.navigator.userAgent.toLowerCase());
  
      $(function(){
          $(window).on('load', function() {
              if(_ua.Mobile) changeSpBtn();
          })
  
          function changeSpBtn() {
              var $footer = $('#footer');
              var $spBtn = $footer.find('.switchBtn');
              var $section = $footer.find('.section.footer-group.bg-gray .footer-group-inner')
  
              if($spBtn.length === 0) return
              $section.append($spBtn);
          }
      })
  })(jQuery);

// ----------------------------------------------------------------------------
// cookie top
// ----------------------------------------------------------------------------
(function($) {
  $(function() {
    var cookieTop = function(ev) {
      $.cookie('contentsCategory', 'top', { path: '/', expires: 90 });
      return true;
    };
    // breadcrumb
    $('#breadcrumbTop, #breadcrumbBtm').find('li:eq(0) a').each(function() {
      var href = this.getAttribute('href');
      if(href === '/index.html' || href === '/') {
        $(this).on('click', cookieTop);
      }
    });
    // class js-cookie-top
    $(document).on('click', '.js-cookie-top', cookieTop);
  });
})(jQuery);

(function($) {
    var coporateAnim = function(el) {
        var $el = el;
        var uaArr = ['ie6', 'ie7', 'ie8'];

        // ie8莉･荳�
        if(uaArr[0] === ua.uaObj.uaBrouser ||
            uaArr[1] === ua.uaObj.uaBrouser ||
            uaArr[2] === ua.uaObj.uaBrouser
            ){
            $el.addClass('is-ie');
        }
    };

    if($('.js-corporate-anim ')[0] !== undefined) {
        coporateAnim($('.js-corporate-anim'));
    }

})(jQuery);

// ----------------------------------------------------------------------------
// lottery
// ----------------------------------------------------------------------------
(function($) {
    $.fn.lotteryResult = function() {
      if(this.length === 0) return false;
      var $this = $(this), cat = null, type = null, path, params = location.search.slice(1).split('&'),
          date, i, k, year = null, month = null, isLatest,
          escHTML = Mzh.escHTML, yearConvert = Mzh.yearConvert, insertComma = Mzh.insertComma, dayJp = Mzh.dayJp;
  
      if($this.hasClass('js-loto')) {
        cat = $this.data('loto-type');
        path = '/retail/takarakuji/loto/' + cat + '/csv/';
      } else if($this.hasClass('js-numbers')) {
        cat = $this.data('numbers-type').replace(/\d+/, '');
        type = +$this.data('numbers-type').replace('numbers', '');
        path = '/retail/takarakuji/' + cat + '/csv/';
      } else if($this.hasClass('js-bingo')) {
        cat = $this.data('bingo-type');
        path = '/retail/takarakuji/bingo/' + cat + '/csv/';
      }
      // 譛亥挨繝舌ャ繧ｯ繝翫Φ繝舌�逕ｨ縺ｫ繝代Λ繝｡繝ｼ繧ｿ蜿門ｾ�
      for(i = 0; i < params.length; i++) {
        var keyValue = params[i].split('=');
        if(keyValue[0] === 'year') {
          year = +escHTML(keyValue[1]);
        } else if(keyValue[0] === 'month') {
          month = +escHTML(keyValue[1]);
        }
      }
      // 繝代Λ繝｡繝ｼ繧ｿ荳榊ｙ縺ｮ讀懷�
      if(!(year === null && month === null) && !(year > 0 && month > 0)) {
        console.log('URL縺梧ｭ｣縺励￥縺ゅｊ縺ｾ縺帙ｓ');
        return false;
      }
      // 1蟷ｴ蛻��蝗槫捷縺ｾ縺ｨ繧，SV蜿門ｾ�
      $.ajax({
        beforeSend: function(xhr){
          xhr.overrideMimeType('text/plain;charset=Shift_JIS');
        },
        type: 'GET',
        dataType: 'text',
        url: path + cat + '.csv?' + (new Date().getTime())
      }).then(
        function(data) {
          // data縺ｮ謨ｴ蠖｢
          var items = data.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
                // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
                return String.fromCharCode(str.charCodeAt(0) - 65248);
              }),
              prefix, i, dateObj, latestDate, latestDay, latestDayJP,
              startNum, endNum,
              issues = [], results = [], timer,
              $condition = $('.js-lottery-condition'), $prize = $condition.find('.js-lottery-prize'), prize = [],
              $bcTopLast = $('#breadcrumbTop li:last-child'), $bcBtmLast = $('#breadcrumbBtm li:last-child'),
              $update = $('.js-lottery-update'), $date = $('.js-lottery-date'), canonical, title;
          // 蜈ｨ隗偵せ繝壹�繧ｹ繧帝勁蜴ｻ
          items = items.replace(/縲/g, '');
          // 譛蠕後�謾ｹ陦碁勁蜴ｻ
          items = items.replace(/(\r\n|\n|\r)$/, '');
          // 繝ｭ繝医�隴伜挨id蜿門ｾ�
          prefix = items.match(/^A5(\d)/)[1];
          // 'A5x'縺ｧ繧ｹ繝励Μ繝�ヨ
          items = items.replace(/^A5\d(\r\n|\n|\r)/, '').split(/(?:\r\n|\n|\r)A5\d(?:\r\n|\n|\r)/);
          for(i = 0; i < items.length; i++) {
            items[i] = items[i].split(/,\s*/);
          }
          // 陦ｨ遉ｺ縺吶ｋ譛医�繝��繧ｿ繧呈歓蜃ｺ
          for(i = 0; i < items.length; i++) {
            // 蟷ｴ譛域律繧貞叙蠕�
            dateObj = yearConvert(items[i][2]);
            if(!dateObj) {
              console.log('蟷ｴ譛域律縺悟叙蠕励〒縺阪∪縺帙ｓ');
              return false;
            }
            // 譛譁ｰ蝗槫捷縺ｮ譎ゅ↓蟷ｴ譛域律菫晏ｭ�
            if(i === 0 && (year === null || (year === dateObj.year && month === dateObj.month))) {
              isLatest = true;
              year = dateObj.year;
              month = dateObj.month;
              latestDate = dateObj.date;
              latestDay = new Date(year, month - 1, latestDate).getDay();
            }
            if(dateObj.year === year && dateObj.month === month) {
              issues.push(items[i]);
            }
          }
          // 謖�ｮ壼ｹｴ譛医�繝��繧ｿ縺後↑縺�
          if(issues.length === 0) {
            console.log('謖�ｮ壹�蟷ｴ譛医�繝��繧ｿ縺ｯ縺ゅｊ縺ｾ縺帙ｓ');
            return false;
          }
          // 陦ｨ遉ｺ縺吶ｋ蝗槫捷縺ｮ逡ｪ蜿ｷ繧貞叙蠕�
          for(i = 0; i < issues.length; i++) {
            if(i === 0) {
              endNum = +issues[i][0].match(/0*(\d+)/)[1];
            }
            if(i === issues.length - 1) {
              startNum = +issues[i][0].match(/0*(\d+)/)[1];
            }
            // 蝗槫捷縺ｮCSV繧貞叙蠕�
            (function(num, index) {
              $.ajax({
                beforeSend: function(xhr){
                  xhr.overrideMimeType('text/plain;charset=Shift_JIS');
                },
                type: 'GET',
                dataType: 'text',
                url: path + 'A10' + prefix + num + '.CSV?' + (new Date().getTime())
              }).then(
                function(data) {
                  // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
                  var item = data.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
                    return String.fromCharCode(str.charCodeAt(0) - 65248);
                  });
                  // 蜈ｨ隗偵せ繝壹�繧ｹ繧帝勁蜴ｻ
                  item = item.replace(/縲/g, '');
                  // 譛蠕後�謾ｹ陦碁勁蜴ｻ
                  item = item.replace(/(\r\n|\n|\r)$/, '');
                  // 謾ｹ陦後〒繧ｹ繝励Μ繝�ヨ
                  item = item.split(/\r\n|\n|\r/);
                  // ,縺ｧ繧ｹ繝励Μ繝�ヨ
                  for(i = 0; i < item.length; i ++) {
                    item[i] = item[i].split(/\s*,\s*/);
                  }
                  results[index] = item;
                },
                function() {
                  console.log('隨ｬ' + num + '蝗槭�繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
                  clearInterval(timer);
                }
              );
            })(issues[i][0].match(/(0*)(\d+)/)[0], i);
          }
          // 蜈ｨ蝗槫捷縺ｮ繝輔ぃ繧､繝ｫ蜿門ｾ励∪縺ｧ繧ｿ繧､繝槭�
          timer = setInterval(function() {
            var isCount = 0, i;
            for(i = 0; i < results.length; i++) {
              isCount += results[i] ? 1 : 0;
            }
            if(isCount === issues.length) {
              clearInterval(timer);
              // DOM縺ｫ繝��繧ｿ蜷舌″蜃ｺ縺�
              var bonusStart = 0, prizeStart, sumStart, conditionStart,
                  $tableTempPC = $('.js-lottery-temp-pc'), clonesPC = [],
                  $divTempSP = $('.js-lottery-temp-sp'), clonesSP = [];
              // 蠖薙○繧捺擅莉ｶ
              switch(cat) {
                case 'miniloto':
                prizeStart = 4;
                conditionStart = 9;
                sumStart = conditionStart - 1;
                break;
                case 'loto6':
                prizeStart = 4;
                conditionStart = 11;
                sumStart = conditionStart - 1;
                break;
                case 'loto7':
                prizeStart = 4;
                conditionStart = 12;
                sumStart = conditionStart - 1;
                break;
                case 'numbers':
                prizeStart = type === 3 ? 4 : 11;
                conditionStart = 16;
                sumStart = type === 3 ? 9 : 15;
                break;
                case 'bingo5':
                prizeStart = 4;
                conditionStart = 12;
                sumStart = 11;
                break;
              }
              for(i = conditionStart; i < results[0].length; i++) {
                var $prizeClone = $prize.clone().removeClass('js-lottery-prize');
                $prizeClone.find('strong').text(results[0][i][0]);
                $prizeClone.find('span').text('縲' + results[0][i][1] + (results[0][i][0].indexOf('繝溘ル') !== -1 ? '�医リ繝ｳ繝舌�繧ｺ3縺ｮ縺ｿ��' : ''));
                prize.push($prizeClone);
              }
              $prize.remove();
              for(i = 0; i < prize.length; i++) {
                $condition.append(prize[i]);
              }
              // 邨先棡繝��繝悶Ν
              for(i = 0; i < results.length; i++) {
                var $clonePC = $tableTempPC.clone().removeClass('js-lottery-temp-pc'),
                    $cloneSP = $divTempSP.clone().removeClass('js-lottery-temp-sp'),
                    adObj, numberAry = [], bonusAry = [];
                // 蝗槫挨
                $clonePC.find('.js-lottery-issue-pc').text('隨ｬ' + results[i][1][0].match(/0*(\d+)/)[1] + '蝗�');
                $cloneSP.find('.js-lottery-issue-sp').text('隨ｬ' + results[i][1][0].match(/0*(\d+)/)[1] + '蝗�');
                // 謚ｽ縺帙ｓ譌･
                adObj = yearConvert(results[i][1][2]);
                $clonePC.find('.js-lottery-date-pc').text(adObj.year + '蟷ｴ' + adObj.month + '譛�' + adObj.date + '譌･');
                $cloneSP.find('.js-lottery-date-sp').text(adObj.year + '蟷ｴ' + adObj.month + '譛�' + adObj.date + '譌･');
                // 譛ｬ謨ｰ蟄� or 謚ｽ縺帙ｓ謨ｰ蟄�
                if(cat.indexOf('loto') !== -1) {
                  // 繝ｭ繝�
                  $clonePC.find('.js-lottery-number-pc').each(function(index) {
                    $(this).text(escHTML(results[i][3][index + 1]));
                    bonusStart = Math.max(bonusStart, index + 1);
                  });
                  for(k = 1; k < results[i][3].length - (cat === 'loto7' ? 3 : 2); k++) {
                    numberAry.push(escHTML(results[i][3][k]));
                  }
                  $cloneSP.find('.js-lottery-number-sp').text(numberAry.join(' '));
                } else if(cat === 'numbers' && type === 3) {
                  // 繝翫Φ繝舌�繧ｺ3
                  $clonePC.find('.js-lottery-number-pc').text(escHTML(results[i][3][1]));
                } else if(cat === 'numbers' && type === 4) {
                  // 繝翫Φ繝舌�繧ｺ4
                  $clonePC.find('.js-lottery-number-pc').text(escHTML(results[i][10][1]));
                } else if(cat === 'bingo5') {
                  // 繝薙Φ繧ｴ5
                  $clonePC.find('.js-lottery-number-pc').each(function(index) {
                    $(this).text(escHTML(results[i][3][index + 1]));
                  });
                  $cloneSP.find('.js-lottery-number-sp').each(function(index) {
                    $(this).text(escHTML(results[i][3][index + 1]));
                  });
                }
                // 繝懊�繝翫せ
                $clonePC.find('.js-lottery-bonus-pc').each(function(index) {
                  $(this).text('(' + escHTML(results[i][3][bonusStart + 2 + index]) + ')');
                });
                for(k = bonusStart + 2; k < results[i][3].length; k++) {
                  bonusAry.push(escHTML(results[i][3][k]));
                }
                $cloneSP.find('.js-lottery-bonus-sp').text(bonusAry.join(' '));
                // 遲臥ｴ壹∝哨縲�≡鬘�
                $clonePC.find('.js-lottery-prize-pc').each(function(index) {
                  $(this).find('th').text(escHTML(results[i][index + prizeStart][0]));
                  $(this).find('td:eq(0)').text(escHTML(insertComma(results[i][index + prizeStart][results[i][index + prizeStart].length - 2])));
                  $(this).find('td:eq(1) strong').text(escHTML(insertComma(results[i][index + prizeStart][results[i][index + prizeStart].length - 1])));
                });
                $cloneSP.find('.js-lottery-prize-sp').each(function(index) {
                  $(this).find('td:eq(0)').text(escHTML(results[i][index + prizeStart][0]));
                  $(this).find('td:eq(1)').text(escHTML(insertComma(results[i][index + prizeStart][results[i][index + prizeStart].length - 2])));
                  $(this).find('td:eq(2)').text(escHTML(insertComma(results[i][index + prizeStart][results[i][index + prizeStart].length - 1])));
                });
                // 雋ｩ螢ｲ螳溽ｸｾ
                $clonePC.find('.js-lottery-sum-pc').text(escHTML(insertComma(results[i][sumStart][1])));
                $cloneSP.find('.js-lottery-sum-sp').text(escHTML(insertComma(results[i][sumStart][1])));
                // 繧ｭ繝｣繝ｪ繝ｼ繧ｪ繝ｼ繝舌�
                $clonePC.find('.js-lottery-over-pc').text(insertComma(escHTML(results[i][sumStart - 1][1])));
                $cloneSP.find('.js-lottery-over-sp').text(insertComma(escHTML(results[i][sumStart - 1][1])));
                // 繧ｯ繝ｭ繝ｼ繝ｳDOM繧帝�蛻励↓縺ｾ縺ｨ繧√ｋ
                clonesPC.push($clonePC);
                clonesSP.push($cloneSP);
              }
              // 繧ｯ繝ｭ繝ｼ繝ｳ縺励◆DOM繧誕ppend縺励※繧ｯ繝ｭ繝ｼ繝ｳ蜈�ｒ蜑企勁
              for(i = 0; i < clonesPC.length; i++) {
                $tableTempPC.parent().append(clonesPC[i]);
              }
              $tableTempPC.remove();
              for(i = 0; i < clonesSP.length; i++) {
                $divTempSP.parent().append(clonesSP[i]);
              }
              $divTempSP.remove();
              $('.js-now-loading').css('display', 'none');
            }
          }, 100);
  
          // canonical
          canonical = document.createElement('link');
          canonical.rel = 'canonical';
          canonical.href = location.href;
          document.getElementsByTagName('head')[0].appendChild(canonical);
          // 繝代Φ縺上★縺ｨ譖ｴ譁ｰ譌･
          if(isLatest) {
            $('#breadcrumbTop li:eq(-2)').hide();
            $('#breadcrumbBtm li:eq(-2)').hide();
            latestDayJP = dayJp(latestDay);
            $update.text('譖ｴ譁ｰ譌･��' + year + '蟷ｴ' + month + '譛�' + latestDate + '譌･ ' + latestDayJP + '譖懈律');
          } else {
            title = $('.h1Tit').text() + '��' + year + '蟷ｴ' + month + '譛茨ｼ�';
            $update.remove();
            $('title').text($('title').text().replace(/^[^|]+|/, function(s1) {
              return title + ' ';
            }));
            $('.h1Tit').text(title);
            $bcTopLast.text(title);
            $bcBtmLast.text(title);
          }
          // 蟷ｴ譛医→謗ｲ霈牙屓蜿ｷ
          $date.text(year + '蟷ｴ' + month + '譛亥� ' + '�育ｬｬ' + (startNum === endNum ? startNum : (startNum + '蝗槭懃ｬｬ' + endNum)) + '蝗橸ｼ�');
        },
        function() {
          console.log('繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
        }
      );
    };
    $(function() {
      $('.js-loto').lotteryResult();
      $('.js-numbers').lotteryResult();
      $('.js-bingo').lotteryResult();
    });
  })(jQuery);

// ----------------------------------------------------------------------------
// lottery backnumber
// ----------------------------------------------------------------------------
(function($) {
  $.fn.lotteryBacknumber = function() {
    if(this.length === 0) return false;
    var $this = $(this), categories = $this.data('lottery-backnumber').split(/\s*,\s*/),
        isLoto = $this.data('lottery-backnumber').indexOf('loto') !== -1,
        isNumbers = $this.data('lottery-backnumber').indexOf('numbers') !== -1,
        isBingo = $this.data('lottery-backnumber').indexOf('bingo') !== -1,
        lists = {}, getTimer = null, i, key,
        yearConvert = Mzh.yearConvert, dayJp = Mzh.dayJp;

    // 繝��繧ｿ縺九ｉDOM逕滓�
    var build = function() {
      var staticPage = {numbers: 2700, miniloto: 520, loto6: 460, loto7: 0, bingo: 0}, isStatic = false, backnumberFile, ele, dir,
          latestTime = 0, latestDate, oldTime = new Date().getTime(), oldDate,
          lastMonth = 0, lastDate, update, minDate = 31, listYear, listMonth,
          lastNum = [], maxLastNum, d, dt, i, k, key,
          $update = $('.js-backnumber-update'),
          $tempA = $('.js-backnumber-temp-a'), $cloneA, $cloneItemsA = [],
          $tempB = $('.js-backnumber-temp-b'), $cloneB, $cloneItemsB = [];
      // 蜷�￥縺倥�荳ｭ縺ｧ譛譁ｰ縺ｮ蟷ｴ譛域律縺ｨ譛蜿､縺ｮ蟷ｴ譛域律
      for(i = 0; i < categories.length; i++) {
        d = yearConvert(lists[categories[i]].data[0][2]);
        dt = new Date(d.year + '/' + d.month + '/' + d.date).getTime();
        if(latestTime < dt) {
          latestTime = dt;
          latestDate = d;
        }
        d = yearConvert(lists[categories[i]].data[lists[categories[i]].data.length - 1][2]);
        dt = new Date(d.year + '/' + d.month + '/' + d.date).getTime();
        if(oldTime > dt) {
          oldTime = dt;
          oldDate = d;
        }
        // 蜷�￥縺倡ｨｮ蛻･縺ｮ邱乗焚繧貞叙蠕�
        lists[categories[i]].total = lists[categories[i]].data.length;
      }
      // 譛譁ｰ縺ｮ蟷ｴ譛医°繧我ｸ逡ｪ蜿､縺�律繧貞叙蠕暦ｼ域峩譁ｰ譌･��
      for(i = 0; i < categories.length; i++) {
        for(k = 0; k < lists[categories[i]].data.length; k++) {
          if(yearConvert(lists[categories[i]].data[k][2]).year === latestDate.year && yearConvert(lists[categories[i]].data[k][2]).month === latestDate.month) {
            if(minDate > yearConvert(lists[categories[i]].data[k][2]).date) {
              minDate = yearConvert(lists[categories[i]].data[k][2]).date;
              update = yearConvert(lists[categories[i]].data[k][2]);
            }
          } else {
            if(lastMonth < yearConvert(lists[categories[i]].data[k][2]).month) {
              lastDate = yearConvert(lists[categories[i]].data[k][2]);
            }
            break;
          }
        }
      }
      // 譖ｴ譁ｰ譌･繧貞渚譏�
      $update.text(lastDate.year + '蟷ｴ' + lastDate.month + '譛亥� 譛邨よ峩譁ｰ譌･ ' + update.year + '蟷ｴ' + update.month + '譛�' + update.date + '譌･ ' + dayJp(new Date(update.year + '/' + update.month + '/' + update.date).getDay()) + '譖懈律');
      // A陦ｨ繝��繝悶Ν縺ｫ蜿肴丐
      for(i = 0; i < latestDate.month + 12 - oldDate.month; i++) {
        $cloneA = $tempA.clone();
        listYear = lastDate.year;
        listMonth = lastDate.month - i;
        // 蟷ｴ蠎ｦ縺悟､峨ｏ繧�
        if(listMonth < 1) {
          listYear --;
          listMonth += 12;
        }
        $cloneA.find('th').text(listYear + '蟷ｴ' + listMonth + '譛亥�');
        $cloneA.find('td').each(function() {
          $(this).find('a').attr('href', $(this).find('a').attr('href') + '?year=' + listYear + '&month=' + listMonth);
        });
        $cloneItemsA.push($cloneA);
      }
      // 繧ｯ繝ｭ繝ｼ繝ｳ縺励◆DOM繧貞�繧後※繝�Φ繝励Ξ繝ｼ繝亥炎髯､
      for(i = 0; i < $cloneItemsA.length; i++) {
        $tempA.parent().append($cloneItemsA[i]);
      }
      $tempA.remove();
      // 驕主悉1蟷ｴ莉･荳翫�諠��ｱ縺ｪ縺�
      if(latestDate.month !== oldDate.month) {
        $('.js-backnumber-b').remove();
        $('.js-now-loading').css('display', 'none');
        return false;
      }
      // B陦ｨ
      // B陦ｨ縺ｮ譛螟ｧ蝗槫捷繧呈歓蜃ｺ
      for(i = 0; i < categories.length; i++) {
        lastNum[i] = +lists[categories[i]].data[lists[categories[i]].total - 1][0].match(/隨ｬ0*(\d+)蝗�/)[1];
      }
      maxLastNum = lastNum[0];
      for(i = 1; i < lastNum.length; i++) {
        maxLastNum = Math.max(maxLastNum, lastNum[i]);
      }
      // B陦ｨ縺ｮ譛螟ｧ蝗槫捷縺ｾ縺ｧ20蝗槫捷縺･縺､
      for(i = 1; i < maxLastNum; i++) {
        var ii = i;
        i += 19;
        if(isLoto) {
          $cloneB = $tempB.clone();
        } else if(isNumbers || isBingo) {
          if(i % 60 === 20) {
            $cloneB = $tempB.clone();
          }
        }
        // 蜷�￥縺倥＃縺ｨ縺ｫ蝗槭☆
        for(k = 0; k < lastNum.length; k++) {
          // 髱咏噪縺ｪ繝壹�繧ｸ繧り��
          isStatic = ii <= staticPage[categories[k]];
          if(isStatic) {
            switch(categories[k]) {
              case 'numbers': backnumberFile = 'num';
              break;
              case 'miniloto': backnumberFile = 'loto';
              break;
              case 'loto6': backnumberFile = 'loto6';
              break;
            }
            backnumberFile += ('0000' + ii).slice(-4);
            backnumberFile += '.html';
          } else {
            if(lastNum[k] - 1 === ii) {
              backnumberFile = 'detail.html?fromto=' + (lastNum[k] - 1);
            } else {
              backnumberFile = 'detail.html?fromto=' + ii + '_' + (lastNum[k] !== null && lastNum[k] > i ? i : lastNum[k] - 1);
            }
            backnumberFile += '&type=' + categories[k];
          }
          // 繝ｭ繝医→繝翫Φ繝舌�繧ｺ縲√ン繝ｳ繧ｴ縺ｨ繝��繝悶Ν邨�′驕輔≧縺ｮ縺ｧ蛻､螳�
          if(isLoto) {
            // 譛蠕後�20蝗槫�縺�°縺ｪ縺�％縺ｨ繧り��
            if(lastNum[k] !== null && lastNum[k] - 1 <= i) {
              $cloneB.find('a').eq(k).attr('href', '/takarakuji/check/loto/backnumber/' + backnumberFile).text('隨ｬ' + ii + ((lastNum[k] - 1 === ii) ? '蝗�' : ('蝗槭懃ｬｬ' + (lastNum[k] - 1) + '蝗�')));
              lastNum[k] = null;
            } else if(lastNum[k] !== null) {
              $cloneB.find('a').eq(k).attr('href', '/takarakuji/check/loto/backnumber/' + backnumberFile).text('隨ｬ' + ii + '蝗槭懃ｬｬ' + i + '蝗�');
            }
          } else if(isNumbers || isBingo) {
            if(i % 60 === 20) {
              ele = $cloneB.find('a').eq(0);
            } else if(i % 60 === 40) {
              ele = $cloneB.find('a').eq(1);
            } else if(i % 60 === 0) {
              ele = $cloneB.find('a').eq(2);
            }
            dir = isNumbers ? 'numbers' : 'bingo';
            if(lastNum[k] !== null && lastNum[k] - 1 <= i) {
              ele.attr('href', '/takarakuji/check/' + dir + '/backnumber/' + backnumberFile).text('隨ｬ' + ii + ((lastNum[k] - 1 === ii) ? '蝗�' : ('蝗槭懃ｬｬ' + (lastNum[k] - 1) + '蝗�')));
              lastNum[k] = null;
            } else if(lastNum[k] !== null) {
              ele.attr('href', '/takarakuji/check/' + dir + '/backnumber/' + backnumberFile).text('隨ｬ' + ii + '蝗槭懃ｬｬ' + i + '蝗�');
            }
            if(maxLastNum <= 21) {
              $cloneB.find('td:eq(1)').remove();
              $cloneB.find('td:eq(1)').remove();
            } else if(maxLastNum <= 41) {
              $cloneB.find('td:eq(2)').remove();
            }
          }
        }
        $cloneItemsB.push($cloneB);
      }
      // 繧ｯ繝ｭ繝ｼ繝ｳ縺励◆DOM繧貞�繧後※繝�Φ繝励Ξ繝ｼ繝亥炎髯､
      for(i = 0; i < $cloneItemsB.length; i++) {
        $tempB.parent().append($cloneItemsB[i]);
      }
      $tempB.remove();
      $('.js-now-loading').css('display', 'none');
    };
    // CSV繝輔ぃ繧､繝ｫ縺ｮ繝ｪ繧ｯ繧ｨ繧ｹ繝�
    for(i = 0; i < categories.length; i++) {
      (function(cat) {
        var path;
        // CSV繝輔ぃ繧､繝ｫ縺ｮ繝代せ
        if(isLoto) {
          path = '/retail/takarakuji/loto/' + cat + '/csv/' + cat + '.csv';
        } else if(isNumbers) {
          path = '/retail/takarakuji/' + cat + '/csv/' + cat + '.csv';
        } else if(isBingo) {
          path = '/retail/takarakuji/bingo/' + cat + '/csv/' + cat + '.csv';
        }
        $.ajax({
          beforeSend: function(xhr){
            xhr.overrideMimeType('text/plain;charset=Shift_JIS');
          },
          type: 'GET',
          dataType: 'text',
          url: path + '?' + (new Date().getTime())
        }).then(
          function(data) {
            var items;
            lists[cat] = {};
            items = data.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
              // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
              return String.fromCharCode(str.charCodeAt(0) - 65248);
            });
            // 蜈ｨ隗偵せ繝壹�繧ｹ繧帝勁蜴ｻ
            items = items.replace(/縲/g, '');
            // 譛蠕後�謾ｹ陦碁勁蜴ｻ
            items = items.replace(/(\r\n|\n|\r)$/, '');
            // 繝ｭ繝医�隴伜挨id蜿門ｾ�
            lists[cat]['prefix'] = items.match(/^A5(\d)/)[1];
            // 'A5x'縺ｧ繧ｹ繝励Μ繝�ヨ
            items = items.replace(/^A5\d(\r\n|\n|\r)/, '').split(/(?:\r\n|\n|\r)A5\d(?:\r\n|\n|\r)/);
            for(i = 0; i < items.length; i++) {
              items[i] = items[i].split(/,\s*/);
            }
            // 驟榊�縺ｫ縺励◆繝��繧ｿ繧呈�ｼ邏�
            lists[cat]['data'] = items;
          },
          function() {
            console.log('繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
            clearInterval(getTimer);
          }
        );
      })(categories[i]);
    }
    // 繝ｪ繧ｯ繧ｨ繧ｹ繝医＠縺溘ヵ繧｡繧､繝ｫ蜈ｨ驛ｨ蜿門ｾ励＠縺溘°繧ｿ繧､繝槭�繧ｻ繝�ヨ
    getTimer = setInterval(function() {
      var count = 0;
      for(key in lists) {
        count ++;
      }
      if(count >= categories.length) {
        clearInterval(getTimer);
        build();
      }
    }, 100);
  };
  $(function() {
    $('.js-lottery-backnumber').lotteryBacknumber();
  });
})(jQuery);

// ----------------------------------------------------------------------------
// lottery backnumber detail
// ----------------------------------------------------------------------------
(function($) {
  $.fn.lotteryBacknumberDetail = function() {
    if(this.length === 0) return false;
    var $this = $(this), type = null, from = null, to = null, params = location.search.slice(1).split('&'),
        typeData = {
          miniloto: {
            word: '繝溘ル繝ｭ繝�',
            prefix: 1,
            prize: 5,
            bonus: 1
          },
          loto6: {
            word: '繝ｭ繝�6',
            prefix: 2,
            prize: 6,
            bonus: 1
          },
          loto7: {
            word: '繝ｭ繝�7',
            prefix: 3,
            prize: 7,
            bonus: 2
          },
          numbers: {
            word: '繝翫Φ繝舌�繧ｺ',
            prefix: 0,
            prize: 7,
            bonus: 0
          },
          bingo5: {
            word: '繝薙Φ繧ｴ5',
            prefix: 4,
            prize: 8,
            bonus: 0
          }
        },
        results = [], timer, isLoto = false, isNumbers = false, isBingo = false, i, k, l,
        escHTML = Mzh.escHTML, yearConvert = Mzh.yearConvert, canonical, title;
    var build = function() {
      var $tempPC = $('.js-lottery-backnumber-temp-pc'),
          $prizeTemp = $('.js-lottery-prize-temp'),
          $bonusTemp = $('.js-lottery-bonus-temp'),
          $tempSP = $('.js-lottery-backnumber-temp-sp'),
          $clonePC, $cloneItemsPC = [], $prizeClone, $prizeCloneItems = [], $bonusClone, $bonusCloneItems = [],
          $bingoPrizeClone, $bingoPrizeCloneItems = [],
          $cloneSP, $cloneItemsSP = [], prizeAry = [], bonusAry = [],
          dataObj, count = 0;
      if(isLoto) {
        // 譛ｬ謨ｰ蟄励�col
        $('.js-lottery-prize-col').attr('colspan', typeData[type].prize);
        // 繝懊�繝翫せ謨ｰ蟄励�col
        $('.js-lottery-bonus-col').attr('colspan', typeData[type].bonus);
      } else if(isBingo) {
        // 譛ｬ謨ｰ蟄励�col
        $('.js-lottery-prize-col').attr('colspan', typeData[type].prize);
      }
      for(i = from; i <= to; i++) {
        // 繧ｯ繝ｭ繝ｼ繝ｳ譬ｼ邏阪ｒ蛻晄悄蛹�
        $prizeCloneItems = [];
        $bonusCloneItems = [];
        $bingoPrizeCloneItems = [];
        prizeAry = [];
        bonusAry = [];
        count = 0;
        $clonePC = $tempPC.clone();
        $cloneSP = $tempSP.clone();
        // 蝗槫捷
        $clonePC.find('th').text('隨ｬ' + i + '蝗�');
        $cloneSP.find('tr:eq(0) td').text('隨ｬ' + i + '蝗�');
        // 蟷ｴ譛域律
        dataObj = yearConvert(results[i - from][1][2]);
        $clonePC.find('.js-lottery-date').text(dataObj.year + '蟷ｴ' + dataObj.month + '譛�' + dataObj.date + '譌･');
        $cloneSP.find('tr:eq(1) td').text(dataObj.year + '蟷ｴ' + dataObj.month + '譛�' + dataObj.date + '譌･');
        if(isLoto) {
          // 譛ｬ謨ｰ蟄�
          for(k = 0; k < typeData[type].prize; k++) {
            $prizeClone = $clonePC.find('.js-lottery-prize-temp').clone();
            $prizeClone.text(results[i - from][3][k + 1]);
            $prizeClone.removeClass('js-lottery-prize-temp');
            $prizeCloneItems.push($prizeClone);
            prizeAry.push(results[i - from][3][k + 1]);
          }
          $cloneSP.find('tr:eq(2) td').text(prizeAry.join(' '));
          // 繝懊�繝翫せ謨ｰ蟄�
          for(l = 0; l < typeData[type].bonus; l++) {
            $bonusClone = $clonePC.find('.js-lottery-bonus-temp').clone();
            $bonusClone.text(results[i - from][3][l + +typeData[type].prize + 2]);
            $bonusClone.removeClass('js-lottery-bonus-temp');
            $bonusCloneItems.push($bonusClone);
            bonusAry.push(results[i - from][3][l + +typeData[type].prize + 2]);
          }
          $cloneSP.find('tr:eq(3) td').text(bonusAry.join(' '));
          // 譛ｬ謨ｰ蟄励√�繝ｼ繝翫せ縺ｮ繧ｯ繝ｭ繝ｼ繝ｳ繧呈諺蜈･縺励※繝�Φ繝励Ξ繝ｼ繝亥炎髯､
          for(k = 0; k < $prizeCloneItems.length; k++) {
            $clonePC.append($prizeCloneItems[k]);
          }
          for(l = 0; l < $bonusCloneItems.length; l++) {
            $clonePC.append($bonusCloneItems[l]);
          }
          $clonePC.find('.js-lottery-prize-temp').remove();
          $clonePC.find('.js-lottery-bonus-temp').remove();
        } else if(isNumbers) {
          $clonePC.find('td:eq(1)').text(results[i - from][3][1]);
          $clonePC.find('td:eq(2)').text(results[i - from][10][1]);
          $cloneSP.find('tr:eq(2) td').text(results[i - from][3][1]);
          $cloneSP.find('tr:eq(3) td').text(results[i - from][10][1]);
        } else if(isBingo) {
          // 譛ｬ謨ｰ蟄�
          for(k = 0; k < typeData[type].prize; k++) {
            $prizeClone = $clonePC.find('.js-lottery-prize-temp').clone();
            $prizeClone.text(results[i - from][3][k + 1]);
            $prizeClone.removeClass('js-lottery-prize-temp');
            $prizeCloneItems.push($prizeClone);
            // prizeAry.push(results[i - from][3][k + 1]);
          }
          // $cloneSP.find('tr:eq(2) td').text(prizeAry.join(' '));
          // 譛ｬ謨ｰ蟄励�繧ｯ繝ｭ繝ｼ繝ｳ繧呈諺蜈･縺励※繝�Φ繝励Ξ繝ｼ繝亥炎髯､
          for(k = 0; k < $prizeCloneItems.length; k++) {
            $clonePC.append($prizeCloneItems[k]);
          }
          $clonePC.find('.js-lottery-prize-temp').remove();
          // SP
          for(k = 0; k < typeData[type].prize + 1; k++) {
            if(k % 3 === 0) {
              $bingoPrizeClone = $cloneSP.find('.js-lottery-prize-row').clone();
              if(k === 0) {
                $bingoPrizeClone.find('th').attr('rowspan', (typeData[type].prize + 1) / 3);
              } else {
                $bingoPrizeClone.find('th').remove();
              }
              $bingoPrizeClone.find('td').eq(k % 3).text(escHTML(results[i - from][3][count + 1]));
            } else if(k % 3 === 1) {
              if(k === 4) {
                $bingoPrizeClone.find('td').eq(k % 3).text('FREE');
                count --;
              } else {
                $bingoPrizeClone.find('td').eq(k % 3).text(escHTML(results[i - from][3][count + 1]));
              }
            } else if(k % 3 === 2) {
              $bingoPrizeClone.find('td').eq(k % 3).text(escHTML(results[i - from][3][count + 1]));
              $bingoPrizeClone.removeClass('js-lottery-prize-row');
              $bingoPrizeCloneItems.push($bingoPrizeClone);
            }
            count ++;
          }
          // 譛ｬ謨ｰ蟄励�繧ｯ繝ｭ繝ｼ繝ｳ繧呈諺蜈･縺励※繝�Φ繝励Ξ繝ｼ繝亥炎髯､
          for(k = 0; k < $bingoPrizeCloneItems.length; k++) {
            $cloneSP.append($bingoPrizeCloneItems[k]);
          }
          $cloneSP.find('.js-lottery-prize-row').remove();
        }
        $cloneItemsPC.push($clonePC);
        $cloneItemsSP.push($cloneSP);
      }
      for(i = 0; i <= (to - from); i++) {
        $tempPC.parent().append($cloneItemsPC[i]);
      }
      $tempPC.remove();
      for(i = 0; i <= (to - from); i++) {
        $tempSP.parent().append($cloneItemsSP[i]);
      }
      $tempSP.remove();
      $('.js-now-loading').css('display', 'none');
    };
    // 縺上§遞ｮ蛻･縺ｨ蝗槫捷繧貞叙蠕�
    for(i = 0; i < params.length; i++) {
      var keyValue = params[i].split('=');
      if(keyValue[0] === 'type') {
        type = escHTML(keyValue[1]);
      } else if(keyValue[0] === 'fromto') {
        from = +keyValue[1].split('_')[0];
        to = +(keyValue[1].split('_')[1] || from);
      }
    }
    if(type === null || from === null || to === null) {
      console.log('URL縺梧ｭ｣縺励￥縺ゅｊ縺ｾ縺帙ｓ');
      return false;
    }
    isLoto = type.indexOf('loto') !== -1;
    isNumbers = type.indexOf('numbers') !== -1;
    isBingo = type.indexOf('bingo') !== -1;
    // 蜷�屓蜿ｷ繧偵Μ繧ｯ繧ｨ繧ｹ繝�
    for(i = from; i <= to; i++) {
      (function(index) {
        var path;
        if(isLoto) {
          path = '/retail/takarakuji/loto/' + type + '/csv/';
        } else if(isNumbers) {
          path = '/retail/takarakuji/' + type + '/csv/';
        } else if(isBingo) {
          path = '/retail/takarakuji/bingo/' + type + '/csv/';
        }
        $.ajax({
          beforeSend: function(xhr){
            xhr.overrideMimeType('text/plain;charset=Shift_JIS');
          },
          type: 'GET',
          dataType: 'text',
          url: path + 'A10' + typeData[type].prefix + ('0000' + index).slice(-4) + '.CSV?' + (new Date().getTime())
        }).then(
          function(data) {
            // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
            var item = data.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
              return String.fromCharCode(str.charCodeAt(0) - 65248);
            });
            // 蜈ｨ隗偵せ繝壹�繧ｹ繧帝勁蜴ｻ
            item = item.replace(/縲/g, '');
            // 譛蠕後�謾ｹ陦碁勁蜴ｻ
            item = item.replace(/(\r\n|\n|\r)$/, '');
            // 謾ｹ陦後〒繧ｹ繝励Μ繝�ヨ
            item = item.split(/\r\n|\n|\r/);
            // ,縺ｧ繧ｹ繝励Μ繝�ヨ
            for(i = 0; i < item.length; i ++) {
              item[i] = item[i].split(/\s*,\s*/);
            }
            results[index - from] = item;
          },
          function() {
            console.log('隨ｬ' + index + '蝗槭�繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
            clearInterval(timer);
          }
        );
      })(i);
    }
    // 繝ｪ繧ｯ繧ｨ繧ｹ繝医＠縺溘ヵ繧｡繧､繝ｫ蜈ｨ驛ｨ蜿門ｾ励＠縺溘°繧ｿ繧､繝槭�繧ｻ繝�ヨ
    timer = setInterval(function() {
      var isCount = 0, i;
      for(i = 0; i < results.length; i++) {
        isCount += results[i] ? 1 : 0;
      }
      if(isCount === to - from + 1) {
        clearInterval(timer);
        build();
      }
    }, 100);
    // canonical
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    canonical.href = location.href;
    document.getElementsByTagName('head')[0].appendChild(canonical);
    // 繧ｿ繧､繝医Ν逕滓�
    title = $('.h1Tit').text().replace(/(\()(\))/, function(s1, s2, s3) {
      return s2 + typeData[type].word + s3;
    });
    title += ' 隨ｬ' + from + '蝗�' + (from === to ? '' : ('縲懃ｬｬ' + to + '蝗�'));
    // 繧ｿ繧､繝医Ν繧貞渚譏�
    $('title').text(title + $('title').text());
    // h1
    $('.h1Tit').text(title);
    // 繝代Φ縺上★
    $('#breadcrumbTop').find('li:last-child').text(title);
    $('#breadcrumbBtm').find('li:last-child').text(title);
  };
  $(function() {
    $('.js-lottery-backnumber-detail').lotteryBacknumberDetail();
  });
})(jQuery);

// ----------------------------------------------------------------------------
// takarakuji
// ----------------------------------------------------------------------------
(function($) {
  $.fn.takarakuji = function() {
    if(this.length === 0) return false;
    // type繝代Λ繝｡繝ｼ繧ｿ繝ｼ縺ｪ縺九▲縺溘ｉ
    if(location.search.indexOf('type=') === -1) {
      console.log('URL縺梧ｭ｣縺励￥縺ゅｊ縺ｾ縺帙ｓ');
      return false;
    }
    var $this = $(this), cat = $this.data('takarakuji'), params = location.search.slice(1).split('&'), type, order, i, escHTML = Mzh.escHTML,
        typeTitle = {
          jumbo: '繧ｸ繝｣繝ｳ繝懷ｮ昴￥縺�',
          zenkoku: '蜈ｨ蝗ｽ騾壼ｸｸ螳昴￥縺�',
          tokyo: '譚ｱ莠ｬ驛ｽ螳昴￥縺�',
          kinki: '霑醍柄螳昴￥縺�',
          chiiki: '蝨ｰ蝓溷現逋らｭ画険闊郁�豐ｻ螳昴￥縺�',
          kct: '髢｢譚ｱ繝ｻ荳ｭ驛ｨ繝ｻ譚ｱ蛹苓�豐ｻ螳昴￥縺�',
          nishinihon: '隘ｿ譌･譛ｬ螳昴￥縺�'
        };
    if(cat === 'result' && location.search.indexOf('order=') === -1) {
      console.log('URL縺梧ｭ｣縺励￥縺ゅｊ縺ｾ縺帙ｓ');
      return false;
    }
    for(i = 0; i < params.length; i++) {
      var keyValue = params[i].split('=');
      if(keyValue[0] === 'type') {
        type = keyValue[1];
      } else if(keyValue[0] === 'order') {
        order = keyValue[1];
      }
    }
    $.ajax({
      beforeSend: function(xhr){
        xhr.overrideMimeType('text/plain;charset=Shift_JIS');
      },
      type: 'GET',
      dataType: 'text',
      url: '/retail/takarakuji/tsujyo/' + type + '/csv/' + type + '.csv?' + (new Date().getTime())
    }).then(
      function(data) {
        // data縺ｮ謨ｴ蠖｢
        var items = data.replace(/[�｡-�ｺ��-�夲ｼ�-�兢/g, function(str) {
          // 蜈ｨ隗定恭謨ｰ蟄励ｒ蜊願ｧ偵↓
          return String.fromCharCode(str.charCodeAt(0) - 65248);
        }), i, title, canonical;
        // 蜈ｨ隗偵せ繝壹�繧ｹ繧帝勁蜴ｻ
        items = items.replace(/縲/g, '');
        // 'A01'縺ｧ繧ｹ繝励Μ繝�ヨ
        items = items.replace(/^A01(\r\n|\n|\r)/, '').split(/(?:\r\n|\n|\r)A01(?:\r\n|\n|\r)/);
        for(i = 0; i < items.length; i++) {
          var k;
          items[i] = items[i].split(/\r\n|\n|\r\s*/);
          for(k = 0; k < items[i].length; k++) {
            items[i][k] = items[i][k].replace(/\s/g, '').split(/,\s*/);
          }
        }
        // canonical
        canonical = document.createElement('link');
        canonical.rel = 'canonical';
        canonical.href = location.href;
        document.getElementsByTagName('head')[0].appendChild(canonical);
        if(cat === 'top') {
          // 譛亥挨繝舌ャ繧ｯ繝翫Φ繝舌�
          // 繧ｿ繧､繝医Ν
          title = typeTitle[type];
          // title
          $('title').text(title + $('title').text());
          // h1
          $this.find('.h1Tit').text(title);
          // 繝代Φ縺上★
          $('#breadcrumbTop').find('li:last-child').text(title);
          $('#breadcrumbBtm').find('li:last-child').text(title);
          // 繝��繝悶Ν譖ｸ縺榊�縺�
          var $tbody = $this.find('tbody'), $rowClone = [];
          for(i = 0; i < items.length; i++) {
            // 蜥梧圜繧定･ｿ證ｦ縺ｫ縺ｪ縺翫☆
            items[i][0][2] = items[i][0][2].replace(/(蟷ｳ謌酢莉､蜥�)(\d+|蜈�)蟷ｴ/, function(str, $1, $2) {
              var baseYear = 0;
              $2 = $2 === '蜈�' ? 1 : $2;
              switch($1) {
                case '蟷ｳ謌�': baseYear = 1988;
                break;
                case '莉､蜥�': baseYear = 2018;
                break;
              }
              return (baseYear + +$2) + '蟷ｴ';
            });
            var $row = $tbody.find('tr').clone();
            $row.find('td:eq(0)').text(escHTML(items[i][0][2]));
            $row.find('td:eq(1)').find('a').attr('href', '/takarakuji/check/tsujyo/result.html?type=' + type + '&order=' + items[i][0][0].match(/隨ｬ(\d+)蝗�/)[1]).text(escHTML(items[i][0][0] + (items[i][0][1] ? '��' + items[i][0][1] + '��' : '')));
            $rowClone.push($row);
          }
          $tbody.find('tr').remove();
          for(k = 0; k < $rowClone.length; k++) {
            $tbody.append($rowClone[k]);
          }
        } else if(cat === 'result') {
          // 蠖薙○繧鍋分蜿ｷ譯亥�
          // 隧ｲ蠖薙�驟榊�繧貞叙繧雁�縺�
          var result = null, subTitle, concatTitle, $bcTop = $('#breadcrumbTop'), $bcBtm = $('#breadcrumbBtm'),
              $detail = $this.find('.js-takarakuji-detail'),
              $tbodyPC = $this.find('.js-takarakuji-table-pc').find('tbody'),
              $tbodySP = $this.find('.js-takarakuji-table-sp').find('tbody'),
              $rowClonePC = [], $rowCloneSP = [], i, k;
          for(i = 0; i < items.length; i++) {
            if(items[i][0][0].indexOf(order) !== -1) {
              result = items[i];
              break;
            }
          }
          title = escHTML(result[0][0]);
          subTitle = escHTML(result[0][1]);
          concatTitle = subTitle ? '��' + subTitle + '��' : '';
          // title
          $('title').text(title + concatTitle + $('title').text());
          // h2
          $this.find('.h2Tit span').text(title + concatTitle);
          // 繝代Φ縺上★
          $bcTop.find('li:eq(-2) a').attr('href', '/takarakuji/check/tsujyo/top.html?type=' + type).text(typeTitle[type]);
          $bcTop.find('li:eq(-1)').text(title + concatTitle);
          $bcBtm.find('li:eq(-2) a').attr('href', '/takarakuji/check/tsujyo/top.html?type=' + type).text(typeTitle[type]);
          $bcBtm.find('li:eq(-1)').text(title + concatTitle);
          // 隧ｳ邏ｰ
          $detail.html((subTitle ? subTitle + '<br>\n' : '') + title + '蠖薙○繧鍋分蜿ｷ<br>\n' + '謚ｽ縺帙ｓ譌･��' + result[0][2] + '<br>\n' + '莨壼�ｴ��' + result[0][3] + '<br>\n' + result[1][0] + '��' + result[1][1]);
          // 蠖薙○繧鍋分蜿ｷ
          for(i = 2; i < result.length; i++) {
            if(!result[i][0]) continue;
            var $rowPC = $tbodyPC.find('tr:eq(0)').clone(),
                $rowPC3rd = $rowPC.find('td:eq(2)'),
                $rowPC4th = $rowPC.find('td:eq(3)'),
                $rowSP = $tbodySP.find('tr:eq(1)').clone();
            // 遲臥ｴ�
            $rowPC.find('td:eq(0)').text(escHTML(result[i][0]));
            $rowSP.find('td:eq(0)').text(escHTML(result[i][0]));
            // 蠖薙○繧馴≡鬘�
            $rowPC.find('td:eq(1)').text(escHTML(result[i][1]));
            $rowSP.find('td:eq(1)').text(escHTML(result[i][1]));
            // 邨�ｼ�PC��
            if(!result[i][3]) {
              // 4逡ｪ逶ｮ縺檎ｩｺ縺ｮ蝣ｴ蜷�
              $rowPC3rd.addClass($rowPC3rd.data('takarakuji-class-empty'));
              $rowPC4th.addClass($rowPC4th.data('takarakuji-class-left')).find('strong').text(escHTML(result[i][2]));
            } else if(result[i][2].slice(-1) === '邨�') {
              $rowPC3rd.addClass($rowPC3rd.data('takarakuji-class-right')).find('strong').text(escHTML(result[i][2]));
            } else {
              $rowPC3rd.addClass($rowPC3rd.data('takarakuji-class-left')).find('strong').text(escHTML(result[i][2]));
            }
            // 逡ｪ蜿ｷ��PC��
            if(/^[0-9]+$/.test(result[i][3])) {
              // 縺吶∋縺ｦ謨ｰ蟄�
              $rowPC4th.addClass($rowPC4th.data('takarakuji-class-right')).find('strong').text(escHTML(result[i][3]) + '逡ｪ');
            } else if(result[i][3]) {
              $rowPC4th.addClass($rowPC4th.data('takarakuji-class-left')).find('strong').text(escHTML(result[i][3]));
            }
            // 邨�/逡ｪ蜿ｷ��SP��
            if(!result[i][3]) {
              $rowSP.find('td:eq(2)').text(escHTML(result[i][2]));
            } else {
              var num = /^[0-9]+$/.test(result[i][3]) ? result[i][3] + '逡ｪ' : result[i][3];
              $rowSP.find('td:eq(2)').html(escHTML(result[i][2]) + '<br>' + escHTML(num));
            }
            $rowClonePC.push($rowPC);
            $rowCloneSP.push($rowSP);
          }
          $tbodyPC.find('tr:eq(0)').remove();
          for(k = 0; k < $rowClonePC.length; k++) {
            $tbodyPC.append($rowClonePC[k]);
          }
          $tbodySP.find('tr:eq(1)').remove();
          for(k = 0; k < $rowCloneSP.length; k++) {
            $tbodySP.append($rowCloneSP[k]);
          }
        }
        $('.js-now-loading').css('display', 'none');
      },
      function() {
        console.log('繝��繧ｿ縺後≠繧翫∪縺帙ｓ');
      }
    );
  };
  $(function() {
    $('.js-takarakuji').takarakuji();
  });
})(jQuery);