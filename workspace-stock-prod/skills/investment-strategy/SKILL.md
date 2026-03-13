---
name: investment-strategy
description: investment-strategy是一个投资策略模块,包含各种投资策略，每个策略都包含一段角色设定和公式分析公式，有其特定的应用场景和优势，你需要更具用户需求，选择合适的投资策略，制定一个具体的买卖策略。
---
# investment-strategy

## 概述
investment-strategy是一个投资策略模块,包含各种投资策略，每个策略都包含一段角色设定和分析公式，有其特定的应用场景和优势，你需要更具用户需求，选择合适的投资策略，制定一个具体的买卖策略。

## 快速开始
要使用investment-strategy模块，您可以按照以下步骤进行：
1. 浏览策略列表，了解每种投资策略的角色设定和分析公式。
2. 根据用户选择的投资策略，来评估和制定一个具体的买卖策略。

## 举个例子
假设用户选择了长期价值投资策略，您可以根据该策略的角色设定和分析公式，制定一个具体的买卖策略。例如，您可以使用公式1中的主力追踪指标来判断买卖点，并结合公式2中的主力进场和洗盘指标来优化买卖决策。通过分析这些指标，您可以制定一个适合用户需求的投资策略，以实现长期价值投资的目标。

## 策略列表
策略列表包含了各种投资策略的详细信息，包括每种策略的角色设定和分析公式。投资策略的分析公式部分包含了各种投资策略的核心公式和计算方法，这些公式可以帮助用户理解每种策略的运作原理和预期收益。以下是一些常见投资策略的示例：

### 长期价值投资策略 
- 角色设定
  - 你是一个喜欢通过主力追踪来判断买卖点，有30年中国股市操盘经验的投资人，会熟练运用通达信指标和量化策略分析股市，喜欢做价值投资，习惯保守投资，买卖周期较长，有明确的投资目标，不会因为短期的盈亏而改变策略。目前有2套通达信公式，可以用于主力追踪，结合这2套公式的优缺点，制定一个买卖策略。
- 分析公式
  - 公式1：
    ```XA_1:=LLV(LOW,30);
    XA_2:=HHV(HIGH,2);
    XA_3:=SMA((CLOSE-XA_1)/(XA_2-XA_1)*100,5,1);
    XA_4:=SMA((XA_2-CLOSE)/(XA_2-XA_1)*100,5,1);
    XA_5:=SMA(MAX(CLOSE-REF(CLOSE,1),0),5,1)/SMA(ABS(CLOSE-REF(CLOSE,1)),5,1)*100;
    XA_6:=EMA(XA_5,3);
    STICKLINE(CLOSE,90,90,1,0),COLOR3C3CFF;
    STICKLINE(CLOSE,50,50,1,0),COLORYELLOW;
    STICKLINE(CLOSE,10,10,1,0),COLORCYAN;
    XA_7:=LLV(LOW,13);
    XA_8:=HHV(HIGH,13);
    XA_9:=SMA((CLOSE-XA_7)/(XA_8-XA_7)*100,5,1);
    XA_10:=SMA((XA_8-CLOSE)/(XA_8-XA_7)*100,5,1);
    XA_11:=XA_9;
    XA_12:=XA_10;
    XA_13:=SMA(MAX(CLOSE-REF(CLOSE,1),0),5,1)/SMA(ABS(CLOSE-REF(CLOSE,1)),5,1)*100;
    XA_14:=EMA(XA_13,3);
    STICKLINE(CLOSE,90,90,1,0),COLOR3C3CFF;
    STICKLINE(CLOSE,50,50,1,0),COLORYELLOW;
    STICKLINE(CLOSE,10,10,1,0),COLORCYAN;
    XA_15:=55;
    XA_16:=34;
    XA_17:=REF(CLOSE,1);
    XA_18:=SMA(MAX(CLOSE-XA_17,0),3,1)/SMA(ABS(CLOSE-XA_17),3,1)*100;
    XA_19:=EMA(CLOSE,3);
    XA_20:=EMA(CLOSE,21);
    AA:=DRAWTEXT(CROSS(85,XA_18),75,3),COLORGREEN;
    XA_21:=IF(YEAR>=2038 AND MONTH>=1,0,1);
    XA_22:=REF(LOW,1)*XA_21;
    XA_23:=SMA(ABS(LOW-XA_22),3,1)/SMA(MAX(LOW-XA_22,0),3,1)*100*XA_21;
    XA_24:=EMA(IF(CLOSE*1.3,XA_23*10,XA_23/10),3)*XA_21;
    XA_25:=LLV(LOW,30)*XA_21;
    XA_26:=HHV(XA_24,30)*XA_21;
    VAR7:=IF(MA(CLOSE,58),1,0)*XA_21;
    VAR8:=EMA(IF(LOW<=XA_25,(XA_24+XA_26*2)/2,0),3)/618*VAR7*XA_21;
    XC:=IF(VAR8>100,100,VAR8)*XA_21,COLORYELLOW;
    庄家吸筹:STICKLINE(XC>(-150),0,XC,8,0),COLORRED;
    XA_27:=100*(HHV(HIGH,55)-CLOSE)/(HHV(HIGH,42)-LLV(LOW,39));
    XA_28:=(CLOSE-LLV(LOW,XA_16))/(HHV(HIGH,XA_16)-LLV(LOW,XA_16))*100;
    XA_29:=SMA(XA_28,3,1);
    XA_30:=SMA(XA_29,3,1);
    XA_31:=3*XA_29-2*XA_30;
    庄家线:EMA(XA_31,6),COLORMAGENTA,LINETHICK4;
    庄家:XA_3,COLORRED;
    散户线:100*(HHV(HIGH,XA_15)-CLOSE)/(HHV(HIGH,XA_15)-LLV(LOW,XA_15)),COLORCYAN,LINETHICK2;
    散户:XA_4,COLORGREEN;
    XA_32:=EMA(XA_31,12);
    XA_33:=EMA(XA_31,55);
    XA_34:=EMA(XA_31,55);
    ```
  - 公式2：
    ```
    VAR1:=REF((LOW+OPEN+CLOSE+HIGH)/4,1);
    VAR2:=SMA(ABS(LOW-VAR1),13,1)/SMA(MAX(LOW-VAR1,0),10,1);
    VAR3:=EMA(VAR2,10);
    VAR4:=LLV(LOW,33);
    VAR5:=EMA(IF(LOW<=VAR4,VAR3,0),3);
    Z:0,COLORBLACK;
    主力进场:IF(VAR5>REF(VAR5,1),VAR5,0),COLORRED,NODRAW;
    洗盘:IF(VAR5<REF(VAR5,1),VAR5,0),COLORGREEN,NODRAW;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,3,0),COLORGREEN;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,3,0 ),COLOR000055;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,2.6,0 ),COLOR000077;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,2.1,0 ),COLOR000099;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,1.5,0 ),COLOR0000BB;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,0.9,0 ),COLOR0000DD;
    STICKLINE(VAR5>REF(VAR5,1),0,VAR5,0.3,0 ),COLOR0000FF;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,3,0),COLOR005500;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,2.6,0),COLOR007700;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,2.1,0),COLOR009900;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,1.5,0),COLOR00BB00;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,0.9,0),COLOR00DD00;
    STICKLINE(VAR5<REF(VAR5,1),0,VAR5,0.3,0),COLOR00FF00;
    VAR21:=SMA(ABS(HIGH-VAR1),13,1)/SMA(MIN(HIGH-VAR1,0),10,1);
    VAR31:=EMA(VAR21,10);
    VAR41:=HHV(HIGH,33);
    VAR51:=EMA(IF(HIGH>=VAR41,VAR31,0),3);
    主力拉高:IF(VAR51<REF(VAR51,1),VAR51,0),COLORYELLOW,NODRAW;
    STICKLINE(VAR51<REF(VAR51,1),0,VAR51,3,0),COLORYELLOW;
    出货:IF(VAR51>REF(VAR51,1),VAR51,0),COLORCYAN,NODRAW;
    STICKLINE(VAR51>REF(VAR51,1),0,VAR51,3,0 ),COLORCYAN;
    ```

